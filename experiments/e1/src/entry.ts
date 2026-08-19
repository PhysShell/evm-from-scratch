/**
 * U-ENTRY — the root frame. Step 2 §3.6, SEM-ROOT-1..7.
 *
 * `U-ENTRY` RETURNS the frame it builds, so every field is its own observable output — unlike
 * `U-CALL`, which passes its frame to a substituted collaborator and whose fields are
 * therefore outside the local observation set. The difference is positional, and it is the
 * clearest illustration of Step 2 §1.2 in the code itself.
 */
import type { Frame, TxContext } from './domain';

export function rootFrame(code: Uint8Array, tx: TxContext): Frame {
  // SEM-ROOT-2/3: absent tx fields read as the zero address, not as undefined.
  const address = tx.to ?? 0n;
  return {
    code,                       // SEM-ROOT-1
    pc: 0,                      // SEM-ROOT-6
    stack: [],                  // SEM-ROOT-7
    memory: new Uint8Array(0),  // SEM-ROOT-7
    address,                    // SEM-ROOT-2
    caller: tx.from ?? 0n,      // SEM-ROOT-3
    static: false,              // SEM-ROOT-5
    storage_owner: address,     // SEM-ROOT-4
    returndata: new Uint8Array(0), // SEM-ROOT-7
  };
}
