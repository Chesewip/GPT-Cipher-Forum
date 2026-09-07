from pathlib import Path
p=Path('outputs/README.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('Start with `template-identifiability-findings.md` for the newest results:', 'Start with `small-update-difference-findings.md`: ciphertext-only entry-change bounds now require at least 18 East1/West1 plaintext differences over 99 positions for anchored three-card updates with a common initial deck, or 11 with arbitrary different initial decks. `template-identifiability-findings.md` covers the preceding results:')
s=s.replace('python verify_action_fold.py\n','python verify_action_fold.py\npython verify_entry_change_bounds.py\npython verify_entry_change_timing.py\n')
p.write_text(s,encoding='utf-8',newline='\r\n')
