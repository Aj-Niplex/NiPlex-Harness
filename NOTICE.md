# Source note

This **public** repo holds user-facing docs and the stable release surface for **Niplex Harness**.

Full development history and agent handover notes live in the **dev** repository:

- Dev: https://github.com/Aj-Niplex/Niplex-Harness  
  (may be renamed to `dev-Niplex-Harness`)

To ship a code release:
1. Stabilize features in the dev repo  
2. Copy the clean package tree here (exclude `AI-handover/`, secrets, personal vault notes)  
3. Tag a version on this public repo  

Until the first full code mirror is finished, treat **dev** as the source of truth for Python modules and this repo as the **docs + packaging front door**.
