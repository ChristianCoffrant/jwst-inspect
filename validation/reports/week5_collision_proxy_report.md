# Week 5 Collision Proxy Report

## Guardrail Metrics

- collision_proxy_shrinkage_count: 0
- safety_path_renames: 0
- task_region_id_renames: 0
- declared_tolerance_m: 0.75
- shrinks_existing_safety_boundary: false

## Proxy Review

| Proxy Path | Visual Target Prim | Declared Tolerance m | Conservative Margin m | Shrinks Existing Safety Boundary |
| --- | --- | ---: | ---: | --- |
| `/World/Safety/CollisionProxies/JWSTBusProxy` | `/World/JWST/Bus` | 0.75 | 0.50 | false |
| `/World/Safety/CollisionProxies/SunshieldProxy` | `/World/JWST/Sunshield` | 0.75 | 0.50 | false |

The Week 5 review records the current conservative proxy contract. It does not shrink keepout, standoff, approach corridor, or collision proxy paths.
