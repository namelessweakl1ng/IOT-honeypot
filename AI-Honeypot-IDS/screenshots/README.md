# Screenshots

This folder holds the screenshots captured during the demo. Each screenshot
referenced in the per-computer READMEs and in `docs/12_Demonstration.md`
should be saved here with a descriptive filename.

## Required screenshots (for the project report)

| #  | Filename                       | Source                                              |
|----|--------------------------------|-----------------------------------------------------|
| 1  | `01_comp1_ip_a.png`            | Computer 1 `ip a` showing 192.168.1.10              |
| 2  | `02_comp1_container_status.png`| Computer 1 `make status` output                     |
| 3  | `03_comp1_sample_log.png`      | Computer 1 `docker logs hp-http \| head -1`         |
| 4  | `04_comp2_elk_status.png`      | Computer 2 `make elk-status` output                 |
| 5  | `05_kibana_overview.png`       | Kibana Overview dashboard, full screen              |
| 6  | `06_kibana_bruteforce.png`     | Kibana Discover filtered to attack_class:bruteforce |
| 7  | `07_kibana_dos_burst.png`      | Kibana timeline showing the DoS burst spike         |
| 8  | `08_comp3_ip_a.png`            | Computer 3 `ip a` showing 192.168.1.30              |
| 9  | `09_comp3_nmap_A.png`          | nmap -A output showing all open ports + banners     |
| 10 | `10_comp3_hydra_cracked.png`   | hydra output showing cracked credentials            |
| 11 | `11_comp3_sqlmap_dump.png`     | sqlmap dumping the users table                      |
| 12 | `12_comp3_pjl_abuse.png`       | netcat PJL abuse response                           |
| 13 | `13_dataset_stats.png`         | `make stats` output (class distribution)            |
| 14 | `14_cv_metrics.png`            | `make train` CV metrics table                       |
| 15 | `15_confusion_matrix.png`      | best model confusion matrix PNG                     |
| 16 | `16_roc_curve.png`             | best model ROC curve PNG                            |
| 17 | `17_trained_models_listing.png`| `ls trained_models/`                                |

## How to capture on Linux

Use `gnome-screenshot`, `scrot`, or `import`:

```bash
# Whole screen
gnome-screenshot -f 01_comp1_ip_a.png

# Active window
gnome-screenshot -w -f 02_comp1_container_status.png

# Specific area
gnome-screenshot -a -f 05_kibana_overview.png
```

Or use Kibana's built-in "Share → PDF reports" for dashboard screenshots.

## Tips

- Crop terminal screenshots to remove unused space.
- Use a dark terminal theme for readability on projectors.
- For Kibana, set the time filter to "Last 15 minutes" and refresh before
  capturing.
- For the confusion matrix and ROC curve PNGs, just copy the files from
  `Computer-2-Analysis/ml/reports/`.
