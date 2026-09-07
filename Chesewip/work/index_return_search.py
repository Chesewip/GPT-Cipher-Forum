from pathlib import Path
p=Path('outputs/README.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('Start with `small-update-difference-findings.md`:', 'The latest continuation is `return-path-search-findings.md`: decomposed exact return constraints now have independently replayed assignments for 195 intervals at rotation 9, with no initial key or plaintext recovered. The stronger ciphertext-only bounds remain in `small-update-difference-findings.md`:')
s=s.replace('python verify_entry_change_timing.py\n','python verify_entry_change_timing.py\npython verify_return_methods.py\npython verify_component_assignments.py\n')
p.write_text(s,encoding='utf-8',newline='\r\n')
