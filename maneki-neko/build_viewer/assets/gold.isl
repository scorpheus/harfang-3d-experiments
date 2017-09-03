in {
	tex2D diffuse_map;
	tex2D specular_map;
	tex2D self_map;
    tex2D env_map;
}

variant {
	vertex {
		out {
			vec3 p;
			vec3 n;
			vec2 v_uv0;	
		}

		source %{
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));

            p = (vModelMatrix * vec4(vPosition, 1.0)).xyz;
            n = normalize(vNormalMatrix * vNormal);

			v_uv0 = vUV0;         
		%}
	}

	pixel {
		source %{
		    #extension GL_NV_shadow_samplers_cube : enable

		    vec3 ambiant_color = vec3(0.25, 0.0, 0.15);

			vec3 e = vec3(0.0, 0.0, 1.0); // p - vViewPosition.xyz;
			vec3 v = normalize(reflect(e, normalize(n)));

			// ----
			// vec4 env_color = texture2D(env_map, v.xy * vec2(1,1));

			// ----
			// float r = sqrt(v.x * v.x + v.z * v.z);

			// float lat = acos(clamp(v.x / r, -1.0, 1.0));
			// lat /= 3.1415926535 * 2.0;
			// if	(v.z > 0.0)
			// 	lat = 1.0 - lat;

			// float lon = asin(v.y) / 3.1415926535 + 0.5;
			// lon = 1.0 - lon;

			// vec4 env_color = texture2D(env_map, vec2(-lat, lon));

			// ----
			float m = 2. * sqrt( pow( v.x, 2. ) + pow( v.y, 2. ) + pow( v.z + 1., 2. ) );
			vec2 vN = v.xy / m + .5;
			vN.y = 1.0 - vN.y;

			vec4 env_color = texture2D(env_map, vN);

			vec3 base_color = texture2D(diffuse_map, v_uv0).xyz;
			vec3 refl_color = texture2D(specular_map, v_uv0).xyz;
			vec3 ior_roughness_occ_color = texture2D(self_map, v_uv0).xyz;
			float diffuse_luma = (base_color.x + base_color.y + base_color.z) * 0.33333;

			/* Standard shader that pretends it is PRB */
			%diffuse% = base_color.xyz;
			%specular% = refl_color.xzy;
			%constant% = ambiant_color * ior_roughness_occ_color.z + env_color.xyz * refl_color * (1.0 - diffuse_luma);

			/* Real PBR shader TODO */
		%}
	}
}
