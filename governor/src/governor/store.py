"""SQLite state for the shadow governor.

Runtime state lives in a plain SQLite database, not in git. Every transition
is a small deterministic function of (current rows, explicit inputs); no
function here reads the wall clock or the network — timestamps are always
passed in by the caller, so every transition is testable offline.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from .model import (
    Carrier,
    EpochState,
    Evidence,
    EvidenceRole,
    Provider,
    ProviderRun,
    ProviderState,
    Rejection,
    RequestState,
    ReviewEpoch,
    Verdict,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS review_epochs (
    epoch_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_id  INTEGER NOT NULL,
    pr_number      INTEGER NOT NULL,
    head_sha       TEXT    NOT NULL,
    base_sha       TEXT    NOT NULL,
    generation     INTEGER NOT NULL,
    state          TEXT    NOT NULL,
    created_at     TEXT    NOT NULL,
    UNIQUE (repository_id, pr_number, generation)
);

CREATE TABLE IF NOT EXISTS provider_runs (
    run_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    epoch_id           INTEGER NOT NULL REFERENCES review_epochs(epoch_id),
    provider           TEXT    NOT NULL,
    generation         INTEGER NOT NULL,
    request_comment_id INTEGER,
    request_state      TEXT    NOT NULL,
    requested_at       TEXT,
    result_state       TEXT    NOT NULL DEFAULT 'PENDING',
    evidence_json      TEXT    NOT NULL DEFAULT '[]',
    rejections_json    TEXT    NOT NULL DEFAULT '[]',
    UNIQUE (epoch_id, provider)
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    delivery_guid TEXT PRIMARY KEY,
    event         TEXT NOT NULL,
    action        TEXT,
    processed_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shadow_verdicts (
    verdict_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    epoch_id          INTEGER NOT NULL REFERENCES review_epochs(epoch_id),
    codex_state       TEXT    NOT NULL,
    coderabbit_state  TEXT    NOT NULL,
    verdict           TEXT    NOT NULL,
    reason            TEXT    NOT NULL,
    computed_at       TEXT    NOT NULL
);
"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- epochs ------------------------------------------------------------

    def _row_to_epoch(self, row: sqlite3.Row) -> ReviewEpoch:
        return ReviewEpoch(
            epoch_id=row["epoch_id"],
            repository_id=row["repository_id"],
            pr_number=row["pr_number"],
            head_sha=row["head_sha"],
            base_sha=row["base_sha"],
            generation=row["generation"],
            state=EpochState(row["state"]),
            requested_at=row["created_at"],
        )

    def current_epoch(self, repository_id: int, pr_number: int) -> Optional[ReviewEpoch]:
        row = self._conn.execute(
            "SELECT * FROM review_epochs WHERE repository_id=? AND pr_number=? "
            "ORDER BY generation DESC LIMIT 1",
            (repository_id, pr_number),
        ).fetchone()
        return self._row_to_epoch(row) if row else None

    def get_epoch(self, epoch_id: int) -> ReviewEpoch:
        row = self._conn.execute(
            "SELECT * FROM review_epochs WHERE epoch_id=?", (epoch_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no epoch {epoch_id}")
        return self._row_to_epoch(row)

    def epoch_by_generation(
        self, repository_id: int, pr_number: int, generation: int
    ) -> Optional[ReviewEpoch]:
        row = self._conn.execute(
            "SELECT * FROM review_epochs WHERE repository_id=? AND pr_number=? "
            "AND generation=?",
            (repository_id, pr_number, generation),
        ).fetchone()
        return self._row_to_epoch(row) if row else None

    def create_epoch(
        self,
        repository_id: int,
        pr_number: int,
        head_sha: str,
        base_sha: str,
        created_at: str,
    ) -> ReviewEpoch:
        """Create the next-generation epoch for a PR.

        The previous ACTIVE epoch (if any) is closed first:
        * different head → STALE (its evidence can never clean the new head);
        * same head → SUPERSEDED (a fresh round was explicitly requested).
        """
        prev = self.current_epoch(repository_id, pr_number)
        if prev is not None and prev.state == EpochState.ACTIVE:
            new_state = (
                EpochState.SUPERSEDED if prev.head_sha == head_sha else EpochState.STALE
            )
            self._set_epoch_state(prev.epoch_id, new_state)
        generation = (prev.generation + 1) if prev else 1
        cur = self._conn.execute(
            "INSERT INTO review_epochs "
            "(repository_id, pr_number, head_sha, base_sha, generation, state, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                repository_id,
                pr_number,
                head_sha,
                base_sha,
                generation,
                EpochState.ACTIVE.value,
                created_at,
            ),
        )
        self._conn.commit()
        return self.get_epoch(cur.lastrowid)

    def _set_epoch_state(self, epoch_id: int, state: EpochState) -> None:
        self._conn.execute(
            "UPDATE review_epochs SET state=? WHERE epoch_id=?",
            (state.value, epoch_id),
        )
        self._conn.commit()

    def mark_stale_on_new_head(
        self, repository_id: int, pr_number: int, new_head_sha: str
    ) -> Optional[ReviewEpoch]:
        """React to a head change (pull_request.synchronize).

        The current ACTIVE epoch for a different head becomes STALE. Returns
        the epoch that was staled, if any. No new round is started here —
        starting a round costs provider quota and is an explicit act (the
        trigger label), not a side effect of every push.
        """
        current = self.current_epoch(repository_id, pr_number)
        if current is None or current.state != EpochState.ACTIVE:
            return None
        if current.head_sha == new_head_sha:
            return None
        self._set_epoch_state(current.epoch_id, EpochState.STALE)
        return self.get_epoch(current.epoch_id)

    # -- provider runs -----------------------------------------------------

    def _row_to_run(self, row: sqlite3.Row) -> ProviderRun:
        return ProviderRun(
            run_id=row["run_id"],
            epoch_id=row["epoch_id"],
            provider=Provider(row["provider"]),
            generation=row["generation"],
            request_state=RequestState(row["request_state"]),
            request_comment_id=row["request_comment_id"],
            requested_at=row["requested_at"],
            result_state=ProviderState(row["result_state"]),
        )

    def create_run(self, epoch: ReviewEpoch, provider: Provider) -> ProviderRun:
        cur = self._conn.execute(
            "INSERT INTO provider_runs (epoch_id, provider, generation, request_state) "
            "VALUES (?,?,?,?)",
            (
                epoch.epoch_id,
                provider.value,
                epoch.generation,
                RequestState.REQUEST_PENDING.value,
            ),
        )
        self._conn.commit()
        return self.get_run(cur.lastrowid)

    def get_run(self, run_id: int) -> ProviderRun:
        row = self._conn.execute(
            "SELECT * FROM provider_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no run {run_id}")
        return self._row_to_run(row)

    def run_for(self, epoch_id: int, provider: Provider) -> Optional[ProviderRun]:
        row = self._conn.execute(
            "SELECT * FROM provider_runs WHERE epoch_id=? AND provider=?",
            (epoch_id, provider.value),
        ).fetchone()
        return self._row_to_run(row) if row else None

    def run_by_request_comment(
        self, repository_id: int, pr_number: int, provider: Provider, comment_id: int
    ) -> Optional[ProviderRun]:
        row = self._conn.execute(
            "SELECT pr.* FROM provider_runs pr JOIN review_epochs re "
            "ON pr.epoch_id = re.epoch_id "
            "WHERE re.repository_id=? AND re.pr_number=? AND pr.provider=? "
            "AND pr.request_comment_id=?",
            (repository_id, pr_number, provider.value, comment_id),
        ).fetchone()
        return self._row_to_run(row) if row else None

    def bind_request(
        self, run_id: int, comment_id: int, requested_at: str
    ) -> ProviderRun:
        self._conn.execute(
            "UPDATE provider_runs SET request_state=?, request_comment_id=?, requested_at=? "
            "WHERE run_id=?",
            (RequestState.REQUEST_BOUND.value, comment_id, requested_at, run_id),
        )
        self._conn.commit()
        return self.get_run(run_id)

    def set_request_state(
        self, run_id: int, state: RequestState, requested_at: Optional[str] = None
    ) -> ProviderRun:
        if requested_at is None:
            self._conn.execute(
                "UPDATE provider_runs SET request_state=? WHERE run_id=?",
                (state.value, run_id),
            )
        else:
            self._conn.execute(
                "UPDATE provider_runs SET request_state=?, requested_at=? WHERE run_id=?",
                (state.value, requested_at, run_id),
            )
        self._conn.commit()
        return self.get_run(run_id)

    def append_evidence(self, run_id: int, evidence: Evidence) -> None:
        row = self._conn.execute(
            "SELECT evidence_json FROM provider_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        items = json.loads(row["evidence_json"])
        items.append(evidence.to_dict())
        self._conn.execute(
            "UPDATE provider_runs SET evidence_json=? WHERE run_id=?",
            (json.dumps(items), run_id),
        )
        self._conn.commit()

    def append_rejection(self, run_id: int, rejection: Rejection) -> None:
        row = self._conn.execute(
            "SELECT rejections_json FROM provider_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        items = json.loads(row["rejections_json"])
        items.append(rejection.to_dict())
        self._conn.execute(
            "UPDATE provider_runs SET rejections_json=? WHERE run_id=?",
            (json.dumps(items), run_id),
        )
        self._conn.commit()

    def evidence_for(self, run_id: int) -> List[Evidence]:
        row = self._conn.execute(
            "SELECT evidence_json FROM provider_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        out: List[Evidence] = []
        for item in json.loads(row["evidence_json"]):
            out.append(
                Evidence(
                    provider=Provider(item["provider"]),
                    carrier=Carrier(item["carrier"]),
                    carrier_id=item["carrier_id"],
                    actor_id=item["actor_id"],
                    actor_login=item["actor_login"],
                    created_at=item["created_at"],
                    classification=ProviderState(item["classification"]),
                    role=EvidenceRole(item["role"]),
                    detail=item["detail"],
                    bound_sha=item["bound_sha"],
                    sha_explicit=item["sha_explicit"],
                    raw_ref=item.get("raw_ref", ""),
                )
            )
        return out

    def rejections_for(self, run_id: int) -> List[dict]:
        row = self._conn.execute(
            "SELECT rejections_json FROM provider_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        return json.loads(row["rejections_json"])

    def set_result_state(self, run_id: int, state: ProviderState) -> ProviderRun:
        self._conn.execute(
            "UPDATE provider_runs SET result_state=? WHERE run_id=?",
            (state.value, run_id),
        )
        self._conn.commit()
        return self.get_run(run_id)

    # -- webhook deliveries ------------------------------------------------

    def record_delivery(
        self, delivery_guid: str, event: str, action: Optional[str], processed_at: str
    ) -> bool:
        """Record a delivery GUID. Returns False if it was already processed.

        GitHub redeliveries reuse the original X-GitHub-Delivery GUID
        (docs: "the X-GitHub-Delivery header will be the same as in the
        original delivery"), so the GUID is a sound idempotency key.
        """
        try:
            self._conn.execute(
                "INSERT INTO webhook_deliveries (delivery_guid, event, action, processed_at) "
                "VALUES (?,?,?,?)",
                (delivery_guid, event, action, processed_at),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    # -- verdicts ----------------------------------------------------------

    def record_verdict(
        self,
        epoch_id: int,
        codex_state: ProviderState,
        coderabbit_state: ProviderState,
        verdict: Verdict,
        reason: str,
        computed_at: str,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO shadow_verdicts "
            "(epoch_id, codex_state, coderabbit_state, verdict, reason, computed_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                epoch_id,
                codex_state.value,
                coderabbit_state.value,
                verdict.value,
                reason,
                computed_at,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def verdicts_for(self, epoch_id: int) -> List[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM shadow_verdicts WHERE epoch_id=? ORDER BY verdict_id",
            (epoch_id,),
        ).fetchall()
