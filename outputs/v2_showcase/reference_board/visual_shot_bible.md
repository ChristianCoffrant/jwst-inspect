# JWST-Inspect v2 Visual Shot Bible

This board grounds the v2 render loop in official NASA/ESA/SVS media. Actual close-up in-space JWST photographs are not claimed; real flight footage is limited and lower-detail than the official visualizations.

| Shot purpose | Primary references | Implementation target |
| --- | --- | --- |
| Real spacecraft-in-space evidence | NASA launch/final view, ESA Ariane 5 separation | Use for silhouette, scale, and honest provenance framing. |
| Mirror close-up | NASA 3D asset, NASA cleanroom mirror photos | Gold segmented mirror with crisp cells, high specular response, and non-flat reflections. |
| Sunshield wide shot | NASA SVS deployment animation, NASA 3D asset, cleanroom sunshield photo | Layered shield, edge detail, believable material roughness, and large deployed silhouette. |
| L2/starfield context | NASA SVS L2 visualization | Black space, subtle starfield, hard solar key light, no gray studio background. |
| Inspector POV | NASA/ESA composition references plus policy trajectories | First-vs-final policy videos from the inspection craft viewpoint. |

## Source Records

### nasa_webb_launch_final_view
- Organization: NASA
- Page: https://science.nasa.gov/mission/webb/launch/
- Local artifact: `outputs/v2_showcase/reference_board/nasa_webb_launch_final_view.webp`
- Intended use: real_in_space_spacecraft_evidence, solar_array_deployment_context, silhouette_reference
- Media capture mode: downloaded_official_page_preview

### esa_webb_separation_video
- Organization: ESA
- Page: https://www.esa.int/ESA_Multimedia/Videos/2021/12/Webb_separation_from_Ariane_5
- Local artifact: `outputs/v2_showcase/reference_board/esa_webb_separation_video.png`
- Intended use: real_in_space_spacecraft_evidence, spacecraft_scale, deployment_geometry
- Media capture mode: official_page_preview_or_placeholder

### esa_hubble_webb_separation_image
- Organization: ESA/Hubble
- Page: https://esahubble.org/images/FHdGeSgX0AoOwbm/
- Local artifact: `outputs/v2_showcase/reference_board/esa_hubble_webb_separation_image.jpg`
- Intended use: real_in_space_spacecraft_evidence, separation_silhouette, spacecraft_scale
- Media capture mode: downloaded_official_page_preview

### nasa_svs_deployment_sequence
- Organization: NASA Scientific Visualization Studio
- Page: https://svs.gsfc.nasa.gov/20339/
- Local artifact: `outputs/v2_showcase/reference_board/nasa_svs_deployment_sequence.jpg`
- Intended use: deployment_geometry, camera_composition, sunshield_shape
- Media capture mode: downloaded_official_page_preview

### nasa_svs_l2_visualization
- Organization: NASA Scientific Visualization Studio
- Page: https://svs.gsfc.nasa.gov/4991/
- Local artifact: `outputs/v2_showcase/reference_board/nasa_svs_l2_visualization.jpg`
- Intended use: l2_space_context, starfield_environment, mission_context
- Media capture mode: downloaded_official_page_preview

### nasa_jwst_3d_resource
- Organization: NASA
- Page: https://science.nasa.gov/3d-resources/james-webb-space-telescope-b/
- Local artifact: `outputs/v2_showcase/reference_board/nasa_jwst_3d_resource.png`
- Intended use: geometry, silhouette, component_layout
- Media capture mode: downloaded_official_page_preview

### nasa_cleanroom_gold_mirror
- Organization: NASA
- Page: https://www.nasa.gov/universe/james-webb-space-telescopes-golden-mirror-unveiled/
- Local artifact: `outputs/v2_showcase/reference_board/nasa_cleanroom_gold_mirror.jpg`
- Intended use: mirror_material, sunshield_material, cleanroom_detail_reference
- Media capture mode: downloaded_official_page_preview
