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
  blurWidth: f32,
  blurHeight: f32,
  blurDir: vec2<f32>,
};

@group(0) @binding(0) var<uniform> U: Uniforms;
@group(0) @binding(1) var srcTex: texture_2d<f32>;
@group(0) @binding(2) var samp: sampler;

// 9-tap Gaussian weights
const w0: f32 = 0.2270270270;
const w1: f32 = 0.1945945946;
const w2: f32 = 0.1216216216;
const w3: f32 = 0.0540540541;
const w4: f32 = 0.0162162162;

@fragment
fn blurFS(@builtin(position) pos: vec4<f32>) -> @location(0) vec4<f32> {
  let uv = pos.xy / vec2<f32>(U.blurWidth, U.blurHeight);
  let texel = 1.0 / vec2<f32>(U.blurWidth, U.blurHeight);
  let dir = U.blurDir; // (1,0) for X or (0,1) for Y

  var sum = textureSample(srcTex, samp, uv).rgb * w0;

  sum += textureSample(srcTex, samp, uv + dir * texel * 1.0).rgb * w1;
  sum += textureSample(srcTex, samp, uv - dir * texel * 1.0).rgb * w1;

  sum += textureSample(srcTex, samp, uv + dir * texel * 2.0).rgb * w2;
  sum += textureSample(srcTex, samp, uv - dir * texel * 2.0).rgb * w2;

  sum += textureSample(srcTex, samp, uv + dir * texel * 3.0).rgb * w3;
  sum += textureSample(srcTex, samp, uv - dir * texel * 3.0).rgb * w3;

  sum += textureSample(srcTex, samp, uv + dir * texel * 4.0).rgb * w4;
  sum += textureSample(srcTex, samp, uv - dir * texel * 4.0).rgb * w4;

  return vec4<f32>(sum, 1.0);
}
