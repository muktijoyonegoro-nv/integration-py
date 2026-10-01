```
================================================================================
                      TEST RUN RESOURCE CONSUMPTION REPORT
================================================================================
  Status:            PASSED
  Duration:          1m 47.74s
  Command:           uv run pytest -p no:warnings -s tests
--------------------------------------------------------------------------------
  HOST TEST RUNNER (Process Tree)
    Peak Memory (RSS):       76.09 MiB
    CPU Time (User / Sys):   5.54s / 3.00s (Total: 8.54s)
    Avg Host CPU Usage:      7.9%
--------------------------------------------------------------------------------
  CONTAINERS (Podman Workloads)
    Containers Observed:     22 (confluent-local (kafka), confluent-local (kafka), confluent-local (kafka), flyway (flyway-sort_mistake), flyway (flyway-sort_mistake), flyway (flyway-sort_service), flyway (flyway-sort_service), mysql (#1), mysql (#2), mysql (#3), redis (#1), redis (redis-sort), redis (redis-sort), redis (redis-sort-mistake), redis (redis-sort-mistake), sort-mistake (#1), sort-mistake (#2), sort-service (#1), sort-service (#2), wiremock (#1), wiremock (#2), wiremock (#3))
    Peak Total Memory:       1.48 GiB
      └─ confluent-local (kafka): 533.68 MiB
      └─ sort-service (#2):     465.11 MiB
      └─ sort-service (#1):     445.08 MiB
      └─ confluent-local (kafka): 415.33 MiB
      └─ confluent-local (kafka): 412.37 MiB
      └─ mysql (#2):            394.25 MiB
      └─ mysql (#1):            384.52 MiB
      └─ mysql (#3):            382.14 MiB
      └─ flyway (flyway-sort_mistake): 141.81 MiB
      └─ flyway (flyway-sort_mistake): 135.42 MiB
      └─ flyway (flyway-sort_service): 134.37 MiB
      └─ flyway (flyway-sort_service): 133.32 MiB
      └─ wiremock (#1):         105.19 MiB
      └─ wiremock (#2):         103.95 MiB
      └─ wiremock (#3):         103.57 MiB
      └─ redis (#1):            8.94 MiB
      └─ sort-mistake (#1):     7.54 MiB
      └─ sort-mistake (#2):     7.04 MiB
      └─ redis (redis-sort):    3.23 MiB
      └─ redis (redis-sort):    3.23 MiB
      └─ redis (redis-sort-mistake): 3.02 MiB
      └─ redis (redis-sort-mistake): 3.02 MiB
    Peak Container CPU:      314.7%
    Peak Concurrent PIDs:    363
    Network I/O (RX / TX):   1.14 MiB / 1.21 MiB
    Block I/O (Read / Write): 14.29 MiB / 354.07 MiB
--------------------------------------------------------------------------------
  DISK & STORAGE DELTA
    Podman Storage Delta:    +0 B (images, containers, volumes)
    Workspace Delta:         +0 B (reports & local files)
    Host Disk Free Delta:    -5.37 MiB
================================================================================
```
