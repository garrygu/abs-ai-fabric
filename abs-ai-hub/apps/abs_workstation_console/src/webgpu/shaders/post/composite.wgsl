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
@group(0) @binding(1) var sceneTex: texture_2d<f32>;
@group(0) @binding(2) var blurTex: texture_2d<f32>;
@group(0) @binding(3) var samp: sampler;

@fragment
fn compositeFS(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
  let uv = pos.xy / U.viewport;
  let base = textureSample(sceneTex, samp, uv).rgb;
  let bloom = textureSample(blurTex, samp, uv).rgb;

  let intensity = mix(0.25, 1.15, U.accent01);
  let outc = base + bloom * intensity;

  return vec4<f32>(outc, 1.0);
}
