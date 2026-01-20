class PaperTextureGenerator {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
    }

    generate(type, intensity, flocculation) {
        // Use window dimensions for the background texture
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;

        if (this.canvas.width === 0 || this.canvas.height === 0) return;

        const { width, height } = this.canvas;
        const imageData = this.ctx.createImageData(width, height);
        const data = imageData.data;

        const paperColors = {
            cream: { r: 244, g: 241, b: 232 },
            smooth: { r: 252, g: 252, b: 250 },
            dark: { r: 24, g: 24, b: 26 } // Dark charcoal for dark mode
        };

        const baseColor = paperColors[type] || paperColors.cream;

        // 1. Generate height map using multi-octave Perlin noise
        const heightMap = new Float32Array(width * height);
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const noise1 = this.noise(x * 0.02, y * 0.02);      // Large features
                const noise2 = this.noise(x * 0.08, y * 0.08) * 0.5; // Medium grain
                const noise3 = this.noise(x * 0.3, y * 0.3) * 0.25;  // Fine grain
                const grain = (Math.random() - 0.5) * 0.1;
                heightMap[y * width + x] = (noise1 + noise2 + noise3 + grain) * intensity;
            }
        }

        // 2. Calculate normals and apply lighting
        const lightAngle = Math.PI / 4;
        const lightX = Math.cos(lightAngle);
        const lightY = Math.sin(lightAngle);

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const h_left = heightMap[y * width + Math.max(0, x - 1)];
                const h_right = heightMap[y * width + Math.min(width - 1, x + 1)];
                const h_up = heightMap[Math.max(0, y - 1) * width + x];
                const h_down = heightMap[Math.min(height - 1, y + 1) * width + x];

                const dx = (h_right - h_left) * 10;
                const dy = (h_down - h_up) * 10;

                const nx = -dx, ny = -dy, nz = 1;
                const normalLength = Math.sqrt(nx * nx + ny * ny + nz * nz);

                const lighting = (nx / normalLength * lightX + ny / normalLength * lightY + nz / normalLength * 0.7);
                const shade = (lighting - 0.5) * 40;

                const index = (y * width + x) * 4;
                data[index] = Math.min(255, Math.max(0, baseColor.r + shade));
                data[index + 1] = Math.min(255, Math.max(0, baseColor.g + shade));
                data[index + 2] = Math.min(255, Math.max(0, baseColor.b + shade));
                data[index + 3] = 255;
            }
        }

        // 3. Add paper flocculation
        if (flocculation > 0) {
            for (let y = 0; y < height; y++) {
                for (let x = 0; x < width; x++) {
                    const flocNoise = this.noise(x * 0.008, y * 0.008) * 12 * flocculation;
                    const index = (y * width + x) * 4;
                    // Apply flocculation safely
                    data[index] = Math.min(255, Math.max(0, data[index] + flocNoise));
                    data[index + 1] = Math.min(255, Math.max(0, data[index + 1] + flocNoise));
                    data[index + 2] = Math.min(255, Math.max(0, data[index + 2] + flocNoise));
                }
            }
        }

        this.ctx.putImageData(imageData, 0, 0);

        // Add spine shadow (spine is in center)
        this.addSpineShadow(width, height);
    }

    addSpineShadow(width, height) {
        // Only if width suggests a spread (desktop)
        if (width < 800) return;

        const gradWidth = 120;
        const centerX = width / 2;
        const gradient = this.ctx.createLinearGradient(centerX - gradWidth / 2, 0, centerX + gradWidth / 2, 0);

        gradient.addColorStop(0, 'rgba(0,0,0,0)');
        gradient.addColorStop(0.3, 'rgba(0,0,0,0.02)');
        gradient.addColorStop(0.5, 'rgba(0,0,0,0.15)'); // Center crease
        gradient.addColorStop(0.7, 'rgba(0,0,0,0.02)');
        gradient.addColorStop(1, 'rgba(0,0,0,0)');

        this.ctx.globalCompositeOperation = 'multiply';
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(centerX - gradWidth / 2, 0, gradWidth, height);
        this.ctx.globalCompositeOperation = 'source-over';
    }

    noise(x, y) {
        if (!this.permutation) this.initPerlin();
        const X = Math.floor(x) & 255;
        const Y = Math.floor(y) & 255;
        x -= Math.floor(x);
        y -= Math.floor(y);
        const u = this.fade(x);
        const v = this.fade(y);
        const A = this.permutation[X] + Y;
        const B = this.permutation[X + 1] + Y;
        return this.lerp(v,
            this.lerp(u, this.grad(this.permutation[A], x, y),
                this.grad(this.permutation[B], x - 1, y)),
            this.lerp(u, this.grad(this.permutation[A + 1], x, y - 1),
                this.grad(this.permutation[B + 1], x - 1, y - 1))
        );
    }

    fade(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
    lerp(t, a, b) { return a + t * (b - a); }
    grad(hash, x, y) {
        const h = hash & 15;
        const u = h < 8 ? x : y;
        const v = h < 4 ? y : (h === 12 || h === 14 ? x : 0);
        return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
    }

    initPerlin() {
        const p = [];
        for (let i = 0; i < 256; i++) p[i] = i;
        for (let i = 255; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [p[i], p[j]] = [p[j], p[i]];
        }
        this.permutation = [...p, ...p];
    }
}
