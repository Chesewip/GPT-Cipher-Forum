from pathlib import Path
p=Path('outputs/README.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('Start with `plaintext-difference-findings.md` for the newest results:', 'Start with `template-identifiability-findings.md` for the newest results: exactly 18 minimum-difference templates for the first 50 East1/West1 symbols, small-alphabet engineered witnesses, a sharp nine-difference construction over 99 symbols, and broader consistency checks. `plaintext-difference-findings.md` develops the preceding results:')
s=s.replace('python verify_weight_dp.py\n','python verify_weight_dp.py\npython verify_compact_templates.py\npython verify_compact_99.py\npython verify_action_fold.py\n')
p.write_text(s,encoding='utf-8',newline='\r\n')
