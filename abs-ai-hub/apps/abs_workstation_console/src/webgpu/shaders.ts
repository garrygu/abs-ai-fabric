/**
 * WebGPU Shaders for Attract Mode visual fabric
 * 
 * Complete WGSL implementation following the shader plan
 */

// ============================================================================
// 1. PARTICLE INTEGRATE (COMPUTE)
// ============================================================================

export const particleComputeShader = `
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

struct Particle {
  pos: vec2<f32>,
  vel: vec2<f32>,
  life: f32,
  seed: f32,
  size: f32,
  _pad: f32,
};

@group(0) @binding(0) var<uniform> U: Uniforms;
@group(0) @binding(1) var<storage, read> PIn: array<Particle>;
@group(0) @binding(2) var<storage, read_write> POut: array<Particle>;
@group(0) @binding(3) var flowTex: texture_2d<f32>;
@group(0) @binding(4) var flowSampler: sampler;

fn hash1(x: f32) -> f32 {
  var n = fract(x * 0.1031);
  n *= n + 33.33;
  n *= n + n;
  return fract(n);
}

fn hash2(p: vec2<f32>) -> vec2<f32> {
  var h = vec3<f32>(p.xyx) * vec3<f32>(0.1031, 0.1030, 0.0973);
  h = fract(h * (h + 33.33));
  return fract((h.xx + h.yz) * h.zy);
}

fn noise2(p: vec2<f32>) -> f32 {
  let i = floor(p);
  let f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  
  let a = hash1(dot(i, vec2<f32>(1.0, 57.0)));
  let b = hash1(dot(i + vec2<f32>(1.0, 0.0), vec2<f32>(1.0, 57.0)));
  let c = hash1(dot(i + vec2<f32>(0.0, 1.0), vec2<f32>(1.0, 57.0)));
  let d = hash1(dot(i + vec2<f32>(1.0, 1.0), vec2<f32>(1.0, 57.0)));
  
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

fn sampleFlow(pos: vec2<f32>) -> vec2<f32> {
  // Normalize pos to 0..1 for texture sampling
  let uv = (pos / U.viewport);
  
  // Sample flow texture (or use analytic curl noise)
  let flow = textureSample(flowTex, flowSampler, uv).xy;
  
  // Analytic curl noise fallback (if texture not available)
  let curl = vec2<f32>(
    sin(pos.x * 0.01 + U.timeSec * 0.5) * cos(pos.y * 0.01),
    -cos(pos.x * 0.01) * sin(pos.y * 0.01 + U.timeSec * 0.5)
  ) * 0.1;
  
  return flow + curl;
}

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= arrayLength(&PIn)) { return; }

  var p = PIn[i];

  // Normalize pos into 0..1 for flow sampling
  let uv = p.pos / U.viewport;

  // --- Forces ---
  let flow = sampleFlow(p.pos);
  let flowStrength = mix(0.15, 1.25, U.gpuUtil01);

  var acc = flow * flowStrength;

  // Attractor for scene 3 ("spinning up")
  if (U.sceneId == 3u) {
    let d = U.center - p.pos;
    let dist = max(length(d), 1.0);
    let dir = d / dist;
    let attract = (1.0 / dist) * mix(0.0, 2.5, U.sceneT01);
    acc += dir * attract;
  }

  // Turbulence (increases with load)
  let t = U.timeSec * 0.35 + p.seed * 10.0;
  let n = vec2<f32>(
    noise2(p.pos * 0.01 + vec2<f32>(t, 0.0)),
    noise2(p.pos * 0.01 + vec2<f32>(0.0, t))
  ) - vec2<f32>(0.5);
  acc += n * mix(0.05, 0.45, U.gpuUtil01);

  // --- Integrate ---
  let dt = U.dtSec;
  p.vel = p.vel + acc * dt;

  // Damping
  p.vel *= mix(0.985, 0.94, U.gpuUtil01);

  p.pos = p.pos + p.vel * (dt * 60.0);

  // Life drift (slow fade; respawn)
  p.life -= dt * 0.02;

  // Wrap / respawn
  let out = (p.pos.x < 0.0 || p.pos.y < 0.0 || p.pos.x > U.viewport.x || p.pos.y > U.viewport.y || p.life <= 0.0);
  if (out) {
    // respawn in a ring or random distribution
    let r1 = hash1(p.seed + U.timeSec);
    let r2 = hash1(p.seed + U.timeSec * 1.7);
    p.pos = vec2<f32>(r1 * U.viewport.x, r2 * U.viewport.y);
    p.vel = vec2<f32>(0.0);
    p.life = 1.0;
    p.size = mix(1.0, 2.5, hash1(p.seed * 3.1));
  }

  POut[i] = p;
}
`

export const flowFieldComputeShader = `
@group(0) @binding(0) var<uniform> params: array<f32, 12>;
@group(0) @binding(1) var<storage, read_write> flowField: texture_storage_2d<rg16float, write>;

@compute @workgroup_size(16, 16)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
  let uv = vec2<f32>(id.xy) / 256.0;
  let gpuUtil = params[0];
  let time = params[5];
  
  // Curl noise / vortex field
  let angle = sin(uv.x * 10.0 + time) * cos(uv.y * 10.0 + time) * 3.14159;
  let strength = 0.1 * (1.0 + gpuUtil * 0.5);
  
  let vel = vec2<f32>(
    cos(angle) * strength,
    sin(angle) * strength
  );
  
  textureStore(flowField, vec2<i32>(id.xy), vec4<f32>(vel, 0.0, 1.0));
}
`

// ============================================================================
// 2. PARTICLE SPRITE RENDER (VERTEX + FRAGMENT)
// ============================================================================

export const particleRenderShader = `
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

struct Particle {
  pos: vec2<f32>,
  vel: vec2<f32>,
  life: f32,
  seed: f32,
  size: f32,
  _pad: f32,
};

struct VSOut {
  @builtin(position) pos: vec4<f32>,
  @location(0) localUV: vec2<f32>,
  @location(1) life: f32,
  @location(2) seed: f32,
};

@group(0) @binding(0) var<uniform> U: Uniforms;
@group(0) @binding(1) var<storage, read> P: array<Particle>;

var<private> quad: array<vec2<f32>, 6> = array<vec2<f32>,6>(
  vec2<f32>(-1.0, -1.0),
  vec2<f32>( 1.0, -1.0),
  vec2<f32>(-1.0,  1.0),
  vec2<f32>(-1.0,  1.0),
  vec2<f32>( 1.0, -1.0),
  vec2<f32>( 1.0,  1.0)
);

@vertex
fn vsMain(
  @builtin(instance_index) iid: u32,
  @builtin(vertex_index) vid: u32
) -> VSOut {
  let p = P[iid];
  let q = quad[vid];          // -1..1 quad
  let size = p.size * mix(1.0, 2.2, U.accent01);

  // screen space position
  let ss = p.pos + q * size;

  // convert to NDC (-1..1)
  let ndc = (ss / U.viewport) * 2.0 - vec2<f32>(1.0, 1.0);
  // flip Y for WebGPU coordinate system
  let clip = vec4<f32>(ndc.x, -ndc.y, 0.0, 1.0);

  var out: VSOut;
  out.pos = clip;
  out.localUV = q;      // keep -1..1 for radial falloff
  out.life = p.life;
  out.seed = p.seed;
  return out;
}

@fragment
fn fsMain(in: VSOut) -> @location(0) vec4<f32> {
  let r = length(in.localUV); // 0 at center
  let soft = smoothstep(1.0, 0.0, r);
  let core = smoothstep(0.35, 0.0, r);  // brighter core

  // base color: cool blue-ish, but you can bias per-scene
  let base = vec3<f32>(0.15, 0.25, 0.6);
  let accent = vec3<f32>(1.0, 0.5, 0.1); // orange highlight

  // mix based on scene accent
  let c = mix(base, accent, U.accent01 * 0.6);

  // intensity: core is bright -> bloom picks it up
  let intensity = soft * 0.35 + core * mix(0.2, 1.2, U.accent01);

  // life fade
  let a = soft * in.life;

  return vec4<f32>(c * intensity, a);
}
`

// ============================================================================
// 3. BLOOM PIPELINE (BRIGHT-PASS + SEPARABLE BLUR + COMPOSITE)
// ============================================================================

export const bloomBrightPassShader = `
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

  let threshold = mix(0.65, 0.35, U.accent01); // more bloom when accent is high
  let knee = 0.2;

  // soft threshold
  let soft = clamp((y - threshold + knee) / (2.0 * knee), 0.0, 1.0);
  let contrib = max(y - threshold, 0.0) + soft * soft * knee;

  let outc = c * (contrib / max(y, 1e-5));
  return vec4<f32>(outc, 1.0);
}
`

export const bloomBlurShader = `
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

// 9-tap Gaussian weights (precomputed)
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
`

export const bloomCompositeShader = `
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
`

export const tonemapGrainShader = `
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
`

