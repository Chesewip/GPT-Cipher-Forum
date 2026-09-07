from pathlib import Path
p=Path('outputs/README.md');s=p.read_text(encoding='utf-8-sig')
s=s.replace('The latest continuation is `return-path-search-findings.md`:', 'Start with `common-deck-search-findings.md`: the saved return-only assignments fail forbidden-return checks; a revised search fits all nine 24-symbol prefixes with one common deck, but no full-corpus key satisfies the plaintext-equality assumptions. `return-path-search-findings.md` records the earlier partial-return results:')
s=s.replace('python verify_component_assignments.py\n','python verify_component_assignments.py\npython verify_nonreturn_refinement.py\npython verify_common_deck_array.py\npython verify_direct_key_search.py\n')
p.write_text(s,encoding='utf-8',newline='\r\n')
