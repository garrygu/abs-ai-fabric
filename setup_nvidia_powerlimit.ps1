schtasks /create /tn "NvidiaSetPowerLimit" /tr "nvidia-smi -pl 300" /sc ONLOGON /rl HIGHEST /f
