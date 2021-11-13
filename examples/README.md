Bootstrap some examples for `geovista`.

At the moment, some examples have publicly available data, some not... sorry about that.

The intention is for this to naturally evolve and mature over time into easily
accessible, repeatable and helpful documented examples, as one might come to 
hope and expect.

This is just the first step on that journey 😉

---

```
examples
├── example_from_1d__synthetic_face_M1_N1.py
│       quad-mesh from contiguous (M+1,)/(N+1,) lat/lon bounds [uniform]{face}
├── example_from_1d__synthetic_node_M1_N1.py
│       quad-mesh from contiguous (M+1,)/(N+1,) lat/lon bounds [uniform]{node}
├── example_from_1d__um.py
│       quad-mesh from contiguous (M, 2)/(N, 2) lat/lon bounds [uniform]{face}
├── example_from_2d__orca.py
│       quad-mesh from (M, N, 4) lat/lon bounds [curvilinear]{face}
├── example_from_2d__synthetic_face_M1N1.py
│       quad-mesh from contiguous (M+1, N+1) lat/lon bounds [uniform]{face}
├── example_from_2d__synthetic_node_M1N1.py
│       quad-mesh from contiguous (M+1, N+1) lat/lon bounds [uniform]{node}
├── example_from_2d__volcello.py
│       quad-mesh from (M, N, 4) lat/lon bounds [rectilinear]{face}
├── example_from_unstructured__fesom.py
│       18-side faced mesh from (N, 18) lat/lon nodes {face}
├── example_from_unstructured__lam.py
│       quad-mesh faced mesh from (N, 4) lat/lon nodes (ugrid){face}
├── example_from_unstructured__lam_apt.py
│       quad-mesh faced mesh from (N, 4) lat/lon nodes (ugrid){face}
├── example_from_unstructured__lfric.py
│       quad-mesh from (N, 4) lat/lon nodes (cube-sphere){face}
├── example_from_unstructured__lfric_orog.py
│       quad-mesh from (N, 4) lat/lon nodes (cubed-sphere){node}
└── example_from_unstructured__lfric_orog_warp.py
        quad-mesh from (N, 4) lat/lon nodes (cubed-sphere){node}
```