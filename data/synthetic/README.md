# Synthetic fixtures

Files here are **generated offline** by `orderflow_lab.synthetic.generate_session`.

- No exchange API calls
- No production captures
- Safe to commit and publish

Regenerate:

```bash
python -c "from pathlib import Path; from orderflow_lab.synthetic import generate_session, write_session_csvs; d,t=generate_session(); write_session_csvs(d,t,Path('.'),'SYNTH_001')"
```
