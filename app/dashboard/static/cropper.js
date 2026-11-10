/**
 * cropper.js - Native HTML5 Canvas Interactive Logo Cropper & Zoom Studio
 * Zero external dependencies. High-DPI Retina support with pre-build header simulation.
 */
(function (window) {
  'use strict';

  class LogoCropperStudio {
    constructor() {
      this.modal = document.getElementById('logoCropperModal');
      this.canvas = document.getElementById('cropCanvas');
      this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
      this.container = document.getElementById('cropCanvasContainer');

      // Controls
      this.zoomSlider = document.getElementById('cropZoomSlider');
      this.zoomValueLabel = document.getElementById('cropZoomValue');
      this.zoomInBtn = document.getElementById('cropZoomInBtn');
      this.zoomOutBtn = document.getElementById('cropZoomOutBtn');
      this.resetFitBtn = document.getElementById('cropResetFitBtn');
      this.rotateCcwBtn = document.getElementById('cropRotateCcwBtn');
      this.rotateCwBtn = document.getElementById('cropRotateCwBtn');
      this.aspectBtns = document.querySelectorAll('.crop-aspect-btn');

      // Pre-Build Preview Elements
      this.headerPreviewBox = document.getElementById('cropHeaderPreviewBox');
      this.headerLogoImg = document.getElementById('cropHeaderLogoImg');
      this.standalonePreviewImg = document.getElementById('cropStandalonePreviewImg');
      this.themeLightBtn = document.getElementById('previewThemeLightBtn');
      this.themeDarkBtn = document.getElementById('previewThemeDarkBtn');
      this.metricDims = document.getElementById('cropMetricDims');
      this.metricAspect = document.getElementById('cropMetricAspect');
      this.brandNameDisplay = document.getElementById('cropHeaderBrandName');
      this.taglineDisplay = document.getElementById('cropHeaderTagline');

      // Modal Actions
      this.closeBtn = document.getElementById('closeCropperModalBtn');
      this.cancelBtn = document.getElementById('cancelCropperBtn');
      this.applyBtn = document.getElementById('applyCroppedLogoBtn');

      // Internal State
      this.image = null;
      this.imageLoaded = false;
      this.zoom = 0; // 0 to 100
      this.panX = 0;
      this.panY = 0;
      this.rotation = 0; // 0, 90, 180, 270
      this.aspectRatio = '4:1'; // '4:1', '3:1', '2:1', '1:1', 'free'
      this.cropBox = { x: 0, y: 0, width: 0, height: 0 };
      this.isDragging = false;
      this.dragStartX = 0;
      this.dragStartY = 0;
      this.initialPanX = 0;
      this.initialPanY = 0;
      this.previewDebounceTimer = null;
      this.onApplyCallback = null;

      this.initEvents();
    }

    initEvents() {
      if (!this.canvas || !this.modal) return;

      // Close handlers
      if (this.closeBtn) this.closeBtn.addEventListener('click', () => this.close());
      if (this.cancelBtn) this.cancelBtn.addEventListener('click', () => this.close());

      // Backdrop escape key
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isOpen()) {
          this.close();
        }
      });

      // Zoom slider
      if (this.zoomSlider) {
        this.zoomSlider.addEventListener('input', (e) => {
          this.setZoom(parseFloat(e.target.value));
        });
      }

      // Step buttons
      if (this.zoomInBtn) {
        this.zoomInBtn.addEventListener('click', () => {
          this.setZoom(Math.min(100, this.zoom + 10));
        });
      }
      if (this.zoomOutBtn) {
        this.zoomOutBtn.addEventListener('click', () => {
          this.setZoom(Math.max(0, this.zoom - 10));
        });
      }

      // Reset / Center
      if (this.resetFitBtn) {
        this.resetFitBtn.addEventListener('click', () => {
          this.panX = 0;
          this.panY = 0;
          this.setZoom(0);
        });
      }

      // Rotation buttons
      if (this.rotateCcwBtn) {
        this.rotateCcwBtn.addEventListener('click', () => {
          this.rotation = (this.rotation - 90 + 360) % 360;
          this.render();
          this.updateLiveHeaderPreview();
        });
      }
      if (this.rotateCwBtn) {
        this.rotateCwBtn.addEventListener('click', () => {
          this.rotation = (this.rotation + 90) % 360;
          this.render();
          this.updateLiveHeaderPreview();
        });
      }

      // Aspect ratio buttons
      if (this.aspectBtns) {
        this.aspectBtns.forEach((btn) => {
          btn.addEventListener('click', () => {
            this.aspectBtns.forEach((b) => {
              b.classList.remove('btn-primary', 'active');
              b.classList.add('btn-secondary');
            });
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-primary', 'active');
            this.aspectRatio = btn.dataset.aspect || '4:1';
            this.calculateCropBox();
            this.render();
            this.updateLiveHeaderPreview();
          });
        });
      }

      // Header Theme Light / Dark Toggles
      if (this.themeLightBtn && this.themeDarkBtn) {
        this.themeLightBtn.addEventListener('click', () => {
          this.themeLightBtn.classList.remove('btn-secondary');
          this.themeLightBtn.classList.add('btn-primary');
          this.themeDarkBtn.classList.remove('btn-primary');
          this.themeDarkBtn.classList.add('btn-secondary');
          this.applyPreviewTheme('light');
        });
        this.themeDarkBtn.addEventListener('click', () => {
          this.themeDarkBtn.classList.remove('btn-secondary');
          this.themeDarkBtn.classList.add('btn-primary');
          this.themeLightBtn.classList.remove('btn-primary');
          this.themeLightBtn.classList.add('btn-secondary');
          this.applyPreviewTheme('dark');
        });
      }

      // Mouse & Touch Pan Handling
      this.canvas.addEventListener('mousedown', (e) => this.onDragStart(e.clientX, e.clientY));
      window.addEventListener('mousemove', (e) => this.onDragMove(e.clientX, e.clientY));
      window.addEventListener('mouseup', () => this.onDragEnd());

      this.canvas.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
          const t = e.touches[0];
          this.onDragStart(t.clientX, t.clientY);
        }
      }, { passive: true });

      window.addEventListener('touchmove', (e) => {
        if (this.isDragging && e.touches.length === 1) {
          const t = e.touches[0];
          this.onDragMove(t.clientX, t.clientY);
        }
      }, { passive: true });

      window.addEventListener('touchend', () => this.onDragEnd());

      // Mouse Wheel Zoom
      this.canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 5 : -5;
        this.setZoom(Math.max(0, Math.min(100, this.zoom + delta)));
      }, { passive: false });

      // Apply Button
      if (this.applyBtn) {
        this.applyBtn.addEventListener('click', () => this.handleApply());
      }
    }

    isOpen() {
      return this.modal && this.modal.style.display !== 'none';
    }

    applyPreviewTheme(mode) {
      if (!this.headerPreviewBox) return;
      const simTop = document.getElementById('previewSimTopBar');
      const brandText = document.getElementById('cropHeaderBrandName');
      const brandTag = document.getElementById('cropHeaderTagline');
      const navLinks = document.getElementById('previewSimNavLinks');

      if (mode === 'dark') {
        this.headerPreviewBox.style.background = '#0f172a';
        this.headerPreviewBox.style.borderColor = 'rgba(56, 189, 248, 0.3)';
        if (simTop) {
          simTop.style.borderColor = 'rgba(255, 255, 255, 0.08)';
          simTop.style.color = '#94a3b8';
        }
        if (brandText) brandText.style.color = '#f8fafc';
        if (brandTag) brandTag.style.color = '#cbd5e1';
        if (navLinks) navLinks.style.color = '#cbd5e1';
      } else {
        this.headerPreviewBox.style.background = '#ffffff';
        this.headerPreviewBox.style.borderColor = '#e2e8f0';
        if (simTop) {
          simTop.style.borderColor = '#f1f5f9';
          simTop.style.color = '#64748b';
        }
        if (brandText) brandText.style.color = '#1c1917';
        if (brandTag) brandTag.style.color = '#78716c';
        if (navLinks) navLinks.style.color = '#475569';
      }
    }

    open(source, options = {}) {
      if (!this.modal) return;
      this.onApplyCallback = options.onApply || null;

      // Update brand text in preview if provided
      if (options.brandName && this.brandNameDisplay) {
        this.brandNameDisplay.textContent = options.brandName;
      }
      if (options.tagline && this.taglineDisplay) {
        this.taglineDisplay.textContent = options.tagline;
      }

      // Reset state
      this.zoom = 0;
      this.panX = 0;
      this.panY = 0;
      this.rotation = 0;
      this.aspectRatio = options.aspectRatio || '4:1';
      if (this.zoomSlider) this.zoomSlider.value = 0;
      if (this.zoomValueLabel) this.zoomValueLabel.textContent = '0%';

      // Reset aspect pills
      if (this.aspectBtns) {
        this.aspectBtns.forEach((b) => {
          if ((b.dataset.aspect || '4:1') === this.aspectRatio) {
            b.classList.remove('btn-secondary');
            b.classList.add('btn-primary', 'active');
          } else {
            b.classList.remove('btn-primary', 'active');
            b.classList.add('btn-secondary');
          }
        });
      }

      this.modal.style.display = 'flex';

      // Load image
      this.loadImage(source);
    }

    close() {
      if (this.modal) {
        this.modal.style.display = 'none';
      }
      this.image = null;
      this.imageLoaded = false;
      this.onApplyCallback = null;
    }

    loadImage(source) {
      if (!source) return;
      const img = new Image();
      img.crossOrigin = 'anonymous';

      img.onload = () => {
        this.image = img;
        this.imageLoaded = true;
        this.panX = 0;
        this.panY = 0;
        this.zoom = 0;
        if (this.zoomSlider) this.zoomSlider.value = 0;
        if (this.zoomValueLabel) this.zoomValueLabel.textContent = '0%';
        this.calculateCropBox();
        this.render();
        this.updateLiveHeaderPreview();
      };

      img.onerror = () => {
        console.error('Failed to load image into Logo Cropper Studio.');
        if (window.showToast) {
          window.showToast('Could not load logo image for cropping.', 'error');
        }
      };

      if (typeof source === 'string') {
        img.src = source;
      } else if (source instanceof File || source instanceof Blob) {
        const reader = new FileReader();
        reader.onload = (e) => {
          img.src = e.target.result;
        };
        reader.readAsDataURL(source);
      }
    }

    calculateCropBox() {
      if (!this.canvas) return;
      const cw = this.canvas.width;
      const ch = this.canvas.height;
      const padding = 24;
      const availW = cw - padding * 2;
      const availH = ch - padding * 2;

      let ratio = 4.0; // default 4:1
      if (this.aspectRatio === '3:1') ratio = 3.0;
      else if (this.aspectRatio === '2:1') ratio = 2.0;
      else if (this.aspectRatio === '1:1') ratio = 1.0;
      else if (this.aspectRatio === 'free') {
        if (this.image && this.image.width > 0 && this.image.height > 0) {
          ratio = this.image.width / this.image.height;
        } else {
          ratio = 3.5;
        }
      }

      let boxW = availW;
      let boxH = boxW / ratio;

      if (boxH > availH) {
        boxH = availH;
        boxW = boxH * ratio;
      }

      this.cropBox = {
        x: Math.round((cw - boxW) / 2),
        y: Math.round((ch - boxH) / 2),
        width: Math.round(boxW),
        height: Math.round(boxH),
      };

      if (this.metricAspect) {
        this.metricAspect.textContent = `${this.aspectRatio} (${this.aspectRatio === '4:1' ? 'Header' : this.aspectRatio === '1:1' ? 'Square' : 'Custom'})`;
      }
    }

    setZoom(val) {
      this.zoom = Math.max(0, Math.min(100, val));
      if (this.zoomSlider) this.zoomSlider.value = this.zoom;
      if (this.zoomValueLabel) this.zoomValueLabel.textContent = `${Math.round(this.zoom)}%`;
      this.render();
      this.debouncedPreviewUpdate();
    }

    onDragStart(clientX, clientY) {
      if (!this.imageLoaded) return;
      this.isDragging = true;
      this.dragStartX = clientX;
      this.dragStartY = clientY;
      this.initialPanX = this.panX;
      this.initialPanY = this.panY;
      if (this.container) this.container.style.cursor = 'grabbing';
    }

    onDragMove(clientX, clientY) {
      if (!this.isDragging || !this.imageLoaded) return;
      const dx = clientX - this.dragStartX;
      const dy = clientY - this.dragStartY;
      this.panX = this.initialPanX + dx;
      this.panY = this.initialPanY + dy;
      this.render();
      this.debouncedPreviewUpdate();
    }

    onDragEnd() {
      if (!this.isDragging) return;
      this.isDragging = false;
      if (this.container) this.container.style.cursor = 'grab';
      this.updateLiveHeaderPreview();
    }

    debouncedPreviewUpdate() {
      if (this.previewDebounceTimer) clearTimeout(this.previewDebounceTimer);
      this.previewDebounceTimer = setTimeout(() => {
        this.updateLiveHeaderPreview();
      }, 50);
    }

    render() {
      if (!this.ctx || !this.canvas) return;
      const ctx = this.ctx;
      const cw = this.canvas.width;
      const ch = this.canvas.height;

      // Clear Canvas
      ctx.clearRect(0, 0, cw, ch);

      if (!this.imageLoaded || !this.image) {
        ctx.fillStyle = '#64748b';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Select or load an image to begin cropping', cw / 2, ch / 2);
        return;
      }

      const cb = this.cropBox;

      // Base scale: fit image inside crop box at zoom=0
      const isRotated90 = (this.rotation === 90 || this.rotation === 270);
      const imgW = isRotated90 ? this.image.height : this.image.width;
      const imgH = isRotated90 ? this.image.width : this.image.height;

      const scaleFit = Math.min(cb.width / imgW, cb.height / imgH);
      const scaleCover = Math.max(cb.width / imgW, cb.height / imgH);
      // Continuous scale from fit (0%) to 3.5x cover (100%)
      const minScale = Math.min(scaleFit, scaleCover);
      const currentScale = minScale * (1.0 + (this.zoom / 100) * 3.0);

      // Draw Dimmed Outside Mask
      ctx.save();
      ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
      ctx.fillRect(0, 0, cw, ch);

      // Clip inside crop box
      ctx.beginPath();
      ctx.rect(cb.x, cb.y, cb.width, cb.height);
      ctx.clip();

      // Clear inside cropBox to transparent checkboard
      ctx.clearRect(cb.x, cb.y, cb.width, cb.height);

      // Draw Image in Crop Box
      ctx.save();
      const centerX = cb.x + cb.width / 2 + this.panX;
      const centerY = cb.y + cb.height / 2 + this.panY;
      ctx.translate(centerX, centerY);
      if (this.rotation !== 0) {
        ctx.rotate((this.rotation * Math.PI) / 180);
      }
      ctx.scale(currentScale, currentScale);
      ctx.drawImage(this.image, -this.image.width / 2, -this.image.height / 2);
      ctx.restore();

      // Draw rule-of-thirds grid guides inside crop box
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);

      // Vertical thirds
      ctx.beginPath();
      ctx.moveTo(cb.x + cb.width / 3, cb.y);
      ctx.lineTo(cb.x + cb.width / 3, cb.y + cb.height);
      ctx.moveTo(cb.x + (cb.width * 2) / 3, cb.y);
      ctx.lineTo(cb.x + (cb.width * 2) / 3, cb.y + cb.height);
      // Horizontal thirds
      ctx.moveTo(cb.x, cb.y + cb.height / 3);
      ctx.lineTo(cb.x + cb.width, cb.y + cb.height / 3);
      ctx.moveTo(cb.x, cb.y + (cb.height * 2) / 3);
      ctx.lineTo(cb.x + cb.width, cb.y + (cb.height * 2) / 3);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.restore(); // end clip

      // Draw Crop Box Outline
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2;
      ctx.strokeRect(cb.x, cb.y, cb.width, cb.height);

      // Draw 4 Corner Handles
      const hSize = 8;
      ctx.fillStyle = '#38bdf8';
      ctx.fillRect(cb.x - 2, cb.y - 2, hSize, hSize);
      ctx.fillRect(cb.x + cb.width - hSize + 2, cb.y - 2, hSize, hSize);
      ctx.fillRect(cb.x - 2, cb.y + cb.height - hSize + 2, hSize, hSize);
      ctx.fillRect(cb.x + cb.width - hSize + 2, cb.y + cb.height - hSize + 2, hSize, hSize);
    }

    updateLiveHeaderPreview() {
      if (!this.imageLoaded || !this.image) return;

      const dataUrl = this.getExportDataUrl(320); // 320px width preview slice
      if (!dataUrl) return;

      if (this.headerLogoImg) {
        this.headerLogoImg.src = dataUrl;
      }
      if (this.standalonePreviewImg) {
        this.standalonePreviewImg.src = dataUrl;
      }

      if (this.metricDims && this.cropBox.width > 0) {
        const outW = Math.round(this.cropBox.width);
        const outH = Math.round(this.cropBox.height);
        this.metricDims.textContent = `${outW * 2} × ${outH * 2} px (Retina 2x)`;
      }
    }

    getExportDataUrl(targetWidth = 640) {
      if (!this.imageLoaded || !this.image) return null;

      const cb = this.cropBox;
      if (cb.width <= 0 || cb.height <= 0) return null;

      const isRotated90 = (this.rotation === 90 || this.rotation === 270);
      const imgW = isRotated90 ? this.image.height : this.image.width;
      const imgH = isRotated90 ? this.image.width : this.image.height;

      const scaleFit = Math.min(cb.width / imgW, cb.height / imgH);
      const scaleCover = Math.max(cb.width / imgW, cb.height / imgH);
      const minScale = Math.min(scaleFit, scaleCover);
      const currentScale = minScale * (1.0 + (this.zoom / 100) * 3.0);

      const ratio = cb.height / cb.width;
      const exportW = Math.min(targetWidth, cb.width * 2);
      const exportH = Math.round(exportW * ratio);

      const offCanvas = document.createElement('canvas');
      offCanvas.width = exportW;
      offCanvas.height = exportH;
      const offCtx = offCanvas.getContext('2d');

      const scaleFactor = exportW / cb.width;

      offCtx.save();
      const centerX = (cb.width / 2 + this.panX) * scaleFactor;
      const centerY = (cb.height / 2 + this.panY) * scaleFactor;
      offCtx.translate(centerX, centerY);
      if (this.rotation !== 0) {
        offCtx.rotate((this.rotation * Math.PI) / 180);
      }
      offCtx.scale(currentScale * scaleFactor, currentScale * scaleFactor);
      offCtx.drawImage(this.image, -this.image.width / 2, -this.image.height / 2);
      offCtx.restore();

      // Export as high-quality WebP with PNG fallback
      let dataUrl = offCanvas.toDataURL('image/webp', 0.92);
      if (!dataUrl || !dataUrl.startsWith('data:image/webp')) {
        dataUrl = offCanvas.toDataURL('image/png');
      }
      return dataUrl;
    }

    async handleApply() {
      if (!this.imageLoaded || !this.image) {
        if (window.showToast) window.showToast('No image loaded to apply.', 'warning');
        return;
      }

      if (this.applyBtn) {
        this.applyBtn.disabled = true;
        this.applyBtn.innerHTML = '<span>⏳ Saving Logo...</span>';
      }

      try {
        const croppedDataUrl = this.getExportDataUrl(800); // High-res retina export
        if (this.onApplyCallback) {
          await this.onApplyCallback(croppedDataUrl);
        }
        this.close();
      } catch (err) {
        console.error('Error applying cropped logo:', err);
        if (window.showToast) {
          window.showToast(`Crop Failed: ${err.message}`, 'error');
        }
      } finally {
        if (this.applyBtn) {
          this.applyBtn.disabled = false;
          this.applyBtn.innerHTML = '<span>✓ Apply &amp; Save Logo</span>';
        }
      }
    }
  }

  // Export to global window scope
  window.LogoCropperStudio = LogoCropperStudio;
})(window);
