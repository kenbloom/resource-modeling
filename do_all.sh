#!/usr/bin/env sh

python2 cpu.py RelyOnMiniAOD.json,Run2030.json
python2 data.py RelyOnMiniAOD.json,Run2030.json
python2 events.py RelyOnMiniAOD.json,Run2030.json

mv 'CPU by Type and Capacity.png' ' CPU by Type and Capacity 2030.png'
mv 'CPU by Type.png' ' CPU by Type 2030.png'
mv 'CPU seconds by Type and Capacity.png' ' CPU seconds by Type and Capacity 2030.png'
mv 'CPU seconds by Type.png' ' CPU seconds by Type 2030.png'
mv 'Disk by Tier.png' ' Disk by Tier 2030.png'
mv 'Disk by Year.png' ' Disk by Year 2030.png'
mv 'Produced by Kind.png' ' Produced by Kind 2030.png'
mv 'Produced by Tier.png' ' Produced by Tier 2030.png'
mv 'Tape by Tier.png' 'Tape by Tier 2030.png'
mv 'Tape by Year.png' 'Tape by Year 2030.png'

python2 cpu.py RelyOnMiniAOD.json,Run2024.json
python2 data.py RelyOnMiniAOD.json,Run2024.json
python2 events.py RelyOnMiniAOD.json,Run2024.json

mv 'CPU by Type and Capacity.png' ' CPU by Type and Capacity 2024.png'
mv 'CPU by Type.png' ' CPU by Type 2024.png'
mv 'CPU seconds by Type and Capacity.png' ' CPU seconds by Type and Capacity 2024.png'
mv 'CPU seconds by Type.png' ' CPU seconds by Type 2024.png'
mv 'Disk by Tier.png' ' Disk by Tier 2024.png'
mv 'Disk by Year.png' ' Disk by Year 2024.png'
mv 'Produced by Kind.png' ' Produced by Kind 2024.png'
mv 'Produced by Tier.png' ' Produced by Tier 2024.png'
mv 'Tape by Tier.png' 'Tape by Tier 2024.png'
mv 'Tape by Year.png' 'Tape by Year 2024.png'
