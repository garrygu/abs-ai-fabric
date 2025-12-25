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
@group(0) @binding(1) var sceneColorTex: texture_2d<f32>;
@group(0) @binding(2) var samp: sampler;

fn luma(c: vec3<f32>) -> f32 {
  return dot(c, vec3<f32>(0.2126, 0.7152, 0.0722));
}

@fragment
fn brightPassFS(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
  let uv = pos.xy / U.viewport;
  let c = textureSample(sceneColorTex, samp, uv).rgb;
  let y = luma(c);

  let threshold = mix(0.65, 0.35, U.accent01);
  let knee = 0.2;

  let soft = clamp((y - threshold + knee) / (2.0 * knee), 0.0, 1.0);
  let contrib = max(y - threshold, 0.0) + soft * soft * knee;

  let outc = c * (contrib / max(y, 1e-5));
  return vec4<f32>(outc, 1.0);
}
