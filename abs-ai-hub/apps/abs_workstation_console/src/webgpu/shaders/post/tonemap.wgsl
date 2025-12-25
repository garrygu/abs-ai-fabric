struct Uniforms {
  timeSec: f32,
  dtSec: f32,
  gpuUtil01: f32,
  vramUtil01: f32,
  sceneId: u32,
  sceneT01: f32,
  transitionT01: f32,
  accent01: f32,
  viewport: vec2<f32>,
  center: vec2<f32>,
};

@group(0) @binding(0) var<uniform> U: Uniforms;
@group(0) @binding(1) var hdrTex: texture_2d<f32>;
@group(0) @binding(2) var samp: sampler;

fn random(uv: vec2<f32>) -> f32 {
  return fract(sin(dot(uv, vec2<f32>(12.9898, 78.233))) * 43758.5453);
}

@fragment
fn fs(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
  let uv = pos.xy / U.viewport;
  let hdr = textureSample(hdrTex, samp, uv).rgb;
  
  // Tonemap (Reinhard)
  let tonemapped = hdr / (hdr + vec3<f32>(1.0));
  
  // Film grain
  let grain = random(uv + U.timeSec * 0.1) * 0.02;
  let final = tonemapped + vec3<f32>(grain);
  
  // Vignette
  let dist = length(uv - vec2<f32>(0.5));
  let vignette = 1.0 - smoothstep(0.3, 0.8, dist) * 0.3;
  
  return vec4<f32>(final * vignette, 1.0);
}
