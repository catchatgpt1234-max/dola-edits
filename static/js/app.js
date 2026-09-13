// Dola Edits - Automated Backend Watermark Removal & AI Caption Studio Controller

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        currentFilename: null,
        videoMeta: null,
        autoBbox: null,
        pollInterval: null,
        activeTaskId: null,
        rawVideoUrl: null,
        cleanVideoUrl: null,
        isCurrentlyBurnedVideo: false,
        burnedVideoUrl: null,
        selectedQuality: '1080',
        isBulkStudioMode: false
    };
    window.appState = state;
    window.state = state;

    // DOM Elements - Navigation & Cards
    const dropzone = document.getElementById('dropzone');
    const videoInput = document.getElementById('videoInput');
    const uploadCard = document.getElementById('uploadCard');
    const previewActionCard = document.getElementById('previewActionCard');
    const resultCard = document.getElementById('resultCard');
    const heroSection = document.getElementById('heroSection');
    const btnBackToUpload = document.getElementById('btnBackToUpload');
    const btnClosePreview = document.getElementById('btnClosePreview');
    const btnBackFromResult = document.getElementById('btnBackFromResult');
    const btnCloseResult = document.getElementById('btnCloseResult');
    const btnProcessAnother = document.getElementById('btnProcessAnother');

    // Video Meta Elements
    const videoInfoInline = document.getElementById('videoInfoInline');
    const videoFileName = document.getElementById('videoFileName');
    const metaRes = document.getElementById('metaRes');
    const metaDuration = document.getElementById('metaDuration');
    const metaAudio = document.getElementById('metaAudio');
    const bulkStudioBatchPill = document.getElementById('bulkStudioBatchPill');
    const bulkStudioVideoCount = document.getElementById('bulkStudioVideoCount');
    const bulkVideoPreviewSelect = document.getElementById('bulkVideoPreviewSelect');
    const btnBackText = document.getElementById('btnBackText');
    const bulkMetaRes = document.getElementById('bulkMetaRes');
    const bulkMetaDuration = document.getElementById('bulkMetaDuration');
    const bulkMetaAudio = document.getElementById('bulkMetaAudio');

    // Left (Before) Player Elements
    const previewPlayerContainer = document.getElementById('previewPlayerContainer');
    const previewVideoScreen = document.getElementById('previewVideoScreen');
    const sourceVideo = document.getElementById('sourceVideo');
    const previewOverlayPlayBtn = document.getElementById('previewOverlayPlayBtn');
    const previewControlBar = document.getElementById('previewControlBar');
    const previewSeeker = document.getElementById('previewSeeker');
    const btnPreviewPlayPause = document.getElementById('btnPreviewPlayPause');
    const previewPlayIcon = document.getElementById('previewPlayIcon');
    const previewPauseIcon = document.getElementById('previewPauseIcon');
    const previewTimeDisplay = document.getElementById('previewTimeDisplay');
    const btnPreviewMute = document.getElementById('btnPreviewMute');
    const previewVolIcon = document.getElementById('previewVolIcon');
    const previewMuteIcon = document.getElementById('previewMuteIcon');
    const btnPreviewFullscreen = document.getElementById('btnPreviewFullscreen');
    const previewFsEnterIcon = document.getElementById('previewFsEnterIcon');
    const previewFsExitIcon = document.getElementById('previewFsExitIcon');

    // Feature Toggles (Top Options: Watermark Remove & Caption Add)
    const toggleWatermark = document.getElementById('toggleWatermark');
    const toggleCaption = document.getElementById('toggleCaption');

    // Caption Studio Elements & State
    const captionState = {
        isWatermarkRemoveActive: true,
        isCaptionAddActive: true,
        cues: [],
        style: 'classic',
        size: 'md',
        fontScale: 0.052,
        lineHeight: 1.16,
        posY: 0.07
    };
    window.captionState = captionState;

    const captionStudioPanel = document.getElementById('captionStudioPanel');
    const captionTextInput = document.getElementById('captionTextInput');
    const captionStyleChips = document.getElementById('captionStyleChips');
    const captionSizeSeg = document.getElementById('captionSizeSeg');
    const captionFontScale = document.getElementById('captionFontScale');
    const captionFontScaleVal = document.getElementById('captionFontScaleVal');
    const captionLineHeight = document.getElementById('captionLineHeight');
    const captionLineHeightVal = document.getElementById('captionLineHeightVal');
    const captionPosY = document.getElementById('captionPosY');
    const captionPosYVal = document.getElementById('captionPosYVal');
    const btnCaptionRemoveOnlyWm = document.getElementById('btnCaptionRemoveOnlyWm');
    const btnCaptionEditCombined = document.getElementById('btnCaptionEditCombined');
    const btnCaptionEditText = document.getElementById('btnCaptionEditText');
    const studioBulkFormatBar = document.getElementById('studioBulkFormatBar');
    const studioBulkFormatBadge = document.getElementById('studioBulkFormatBadge');
    const chipStudioSingle = document.getElementById('chipStudioSingle');
    const chipStudioZip = document.getElementById('chipStudioZip');
    const captionDownloadCard = document.getElementById('captionDownloadCard');
    const btnCaptionDownloadLink = document.getElementById('btnCaptionDownloadLink');
    const previewCaptionOverlay = document.getElementById('previewCaptionOverlay');
    const cleanCaptionOverlay = document.getElementById('cleanCaptionOverlay');
    const captionSpeechBadge = document.getElementById('captionSpeechBadge');
    const btnAutoTranscribeVoice = document.getElementById('btnAutoTranscribeVoice');
    const transcribeBtnLabel = document.getElementById('transcribeBtnLabel');

    // Studio Column Elements
    const comparisonStudioGrid = document.querySelector('.comparison-studio-grid');
    const studioColBefore = document.getElementById('studioColBefore');
    const studioColCenter = document.getElementById('studioColCenter');
    const studioColAfter = document.getElementById('studioColAfter');
    const beforeTitlePill = document.getElementById('beforeTitlePill');
    const beforePillDot = document.getElementById('beforePillDot');
    const beforePillLabel = document.getElementById('beforePillLabel');
    const beforePillBadge = document.getElementById('beforePillBadge');

    // Center Action Elements
    const removerInitialWrap = document.getElementById('removerInitialWrap');
    const centerActionsCompleted = document.getElementById('centerActionsCompleted');
    const btnStartAutoProcess = document.getElementById('btnStartAutoProcess');
    const removerBtnText = document.getElementById('removerBtnText');
    const removerStatusSubtext = document.getElementById('removerStatusSubtext');

    // Right (After) Player Elements
    const cleanPlayerContainer = document.getElementById('cleanPlayerContainer');
    const afterPlaceholder = document.getElementById('afterPlaceholder');
    const afterBufferingOverlay = document.getElementById('afterBufferingOverlay');
    const cleanVideoScreen = document.getElementById('cleanVideoScreen');
    const cleanedVideo = document.getElementById('cleanedVideo');
    const overlayPlayBtn = document.getElementById('overlayPlayBtn');
    const externalControlBar = document.getElementById('externalControlBar');
    const videoSeeker = document.getElementById('videoSeeker');
    const btnPlayPause = document.getElementById('btnPlayPause');
    const playIcon = document.getElementById('playIcon');
    const pauseIcon = document.getElementById('pauseIcon');
    const timeDisplay = document.getElementById('timeDisplay');
    const btnMute = document.getElementById('btnMute');
    const volIcon = document.getElementById('volIcon');
    const muteIcon = document.getElementById('muteIcon');
    const btnFullscreen = document.getElementById('btnFullscreen');
    const fsEnterIcon = document.getElementById('fsEnterIcon');
    const fsExitIcon = document.getElementById('fsExitIcon');
    const downloadCleanBtn = document.getElementById('downloadCleanBtn');
    const cleanQualityBadge = document.getElementById('cleanQualityBadge');
    const captionQualityBadge = document.getElementById('captionQualityBadge');
    const actionExportQualityBadge = document.getElementById('actionExportQualityBadge');
    const qualityChips = document.querySelectorAll('.quality-chip');

    // Progress Modal Elements
    const processingModal = document.getElementById('processingModal');
    const progressPercent = document.getElementById('progressPercent');
    const progressCircle = document.getElementById('progressCircle');
    const linearFill = document.getElementById('linearFill');
    const statFrames = document.getElementById('statFrames');
    const statFps = document.getElementById('statFps');
    const statEta = document.getElementById('statEta');
    const statElapsed = document.getElementById('statElapsed');
    const processingStatusText = document.getElementById('processingStatusText');
    const processBufferingBadgeText = document.getElementById('processBufferingBadgeText');

    // Upload & Analysis Progress Modal Elements
    const uploadProgressModal = document.getElementById('uploadProgressModal');
    const uploadProgressPercent = document.getElementById('uploadProgressPercent');
    const uploadProgressCircle = document.getElementById('uploadProgressCircle');
    const uploadLinearFill = document.getElementById('uploadLinearFill');
    const uploadModalTitle = document.getElementById('uploadModalTitle');
    const uploadModalStatusText = document.getElementById('uploadModalStatusText');
    const uploadBufferingBadgeText = document.getElementById('uploadBufferingBadgeText');
    const uploadStatFileName = document.getElementById('uploadStatFileName');
    const uploadStatFileSize = document.getElementById('uploadStatFileSize');
    const uploadStatTime = document.getElementById('uploadStatTime');

    // --- UPLOAD & DRAG/DROP HANDLING ---
    dropzone.addEventListener('click', () => videoInput.click());
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 1) {
            handleBulkFiles(files);
        } else if (files && files.length === 1) {
            handleFileUpload(files[0]);
        }
    });

    videoInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    let uploadTimerInterval = null;
    let uploadAnalysisInterval = null;

    function formatTimeSec(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function setUploadProgress(pct, statusMsg, badgeText) {
        if (uploadProgressPercent) uploadProgressPercent.textContent = `${pct}%`;
        if (uploadLinearFill) uploadLinearFill.style.width = `${pct}%`;
        if (uploadProgressCircle) {
            const circumference = 2 * Math.PI * 42;
            const offset = circumference - (pct / 100) * circumference;
            uploadProgressCircle.style.strokeDashoffset = offset;
        }
        if (statusMsg && uploadModalStatusText) uploadModalStatusText.textContent = statusMsg;
        if (badgeText && uploadBufferingBadgeText) uploadBufferingBadgeText.textContent = badgeText;
    }

    async function handleFileUpload(file) {
        if (!file.type.startsWith('video/') && !file.name.match(/\.(mp4|mov|avi|webm|mkv)$/i)) {
            alert('Please select a valid video file (.mp4, .mov, .webm, .avi)');
            return;
        }

        // Show in-place progress card directly where upload button was
        if (uploadStatFileName) uploadStatFileName.textContent = file.name;
        if (uploadStatFileSize) {
            const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
            uploadStatFileSize.textContent = `${sizeMb} MB`;
        }
        const isCaptionActive = Boolean(captionState && captionState.isCaptionAddActive);

        if (isCaptionActive) {
            // Caption Add Mode: Show AI speech transcription buffering modal
            if (uploadModalTitle) uploadModalTitle.textContent = 'Uploading Video...';
            if (uploadStatTime) uploadStatTime.textContent = '00:00';
            setUploadProgress(0, 'Sending video file to Dola Edits engine...', '⚡ Buffering & Uploading...');
            if (uploadCard) uploadCard.classList.add('hidden');
            if (uploadProgressModal) uploadProgressModal.classList.remove('hidden');

            const uploadStartTime = Date.now();
            if (uploadTimerInterval) clearInterval(uploadTimerInterval);
            uploadTimerInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - uploadStartTime) / 1000);
                if (uploadStatTime) uploadStatTime.textContent = formatTimeSec(elapsed);
            }, 1000);
        } else {
            // Watermark-Only Mode: Direct to Before/After studio without modal (As requested by user!)
            if (uploadProgressModal) uploadProgressModal.classList.add('hidden');
            if (dropzone) dropzone.classList.add('is-direct-uploading');
        }

        const formData = new FormData();
        formData.append('video', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);

        // Real upload progress: 0% to 100% as client sends video bytes to server
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable && isCaptionActive) {
                const uploadPct = Math.min(99, Math.round((e.loaded / e.total) * 100));
                setUploadProgress(uploadPct, `Uploading video (${uploadPct}%)...`, '⚡ Uploading...');
            }
        };

        xhr.upload.onload = () => {
            if (isCaptionActive) {
                setUploadProgress(100, 'Saving video and preparing studio...', '⚡ Finalizing...');
            }
        };

        xhr.onload = () => {
            if (dropzone) dropzone.classList.remove('is-direct-uploading');
            if (uploadTimerInterval) clearInterval(uploadTimerInterval);
            if (uploadAnalysisInterval) clearInterval(uploadAnalysisInterval);

            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (data.success) {
                        if (uploadProgressModal) uploadProgressModal.classList.add('hidden');
                        loadVideoIntoWorkspace(data);
                        return;
                    } else {
                        throw new Error(data.error || 'Failed to analyze video');
                    }
                } catch (err) {
                    if (uploadProgressModal) uploadProgressModal.classList.add('hidden');
                    if (uploadCard) uploadCard.classList.remove('hidden');
                    alert('Upload error: ' + err.message);
                }
            } else {
                if (uploadProgressModal) uploadProgressModal.classList.add('hidden');
                if (uploadCard) uploadCard.classList.remove('hidden');
                alert('Upload failed with server status ' + xhr.status);
            }
        };

        xhr.onerror = () => {
            if (uploadTimerInterval) clearInterval(uploadTimerInterval);
            if (uploadAnalysisInterval) clearInterval(uploadAnalysisInterval);
            if (uploadProgressModal) uploadProgressModal.classList.add('hidden');
            if (uploadCard) uploadCard.classList.remove('hidden');
            alert('Upload network error. Please try again.');
        };

        xhr.send(formData);
    }

    function applyAspectRatio(container, meta) {
        if (!container || !meta) return;
        const w = meta.width;
        const h = meta.height;
        if (!w || !h) return;
        const ratio = w / h;
        container.classList.remove('is-vertical', 'is-horizontal', 'is-square');
        if (ratio < 0.85) {
            container.classList.add('is-vertical');
        } else if (ratio > 1.25) {
            container.classList.add('is-horizontal');
        } else {
            container.classList.add('is-square');
        }
    }

    function loadVideoIntoWorkspace(data) {
        state.currentFilename = data.filename;
        state.videoMeta = data.metadata;
        state.autoBbox = data.auto_bbox;

        if (videoFileName) videoFileName.textContent = data.original_name || data.filename;
        if (metaRes) metaRes.textContent = `${data.metadata.width}x${data.metadata.height}`;
        const mins = Math.floor(data.metadata.duration / 60);
        const secs = Math.floor(data.metadata.duration % 60);
        if (metaDuration) metaDuration.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
        if (metaAudio) metaAudio.textContent = data.metadata.has_audio ? '🔊 Audio Preserved' : '🔇 No Audio';

        state.rawVideoUrl = data.video_url;
        state.serverCleanUrl = data.clean_video_url || null; // Pre-cleaned video cached on upload

        // Single Video with Caption & Watermark Remove:
        // As requested: "jab hi upload kre to pahele watermark remove krna hai uske bad hi caption add krna and fir dawnload"
        if (captionState.isCaptionAddActive && captionState.isWatermarkRemoveActive && data.clean_video_url) {
            state.cleanVideoUrl = data.clean_video_url;
            state.hasUserProcessedWatermark = true;
        } else {
            state.cleanVideoUrl = null;
            state.hasUserProcessedWatermark = false;
        }
        state.isCurrentlyBurnedVideo = false;
        state.burnedVideoUrl = null;

        if (data.filename && downloadCleanBtn) {
            const cleanBase = `/api/download-clean/${data.filename}`;
            downloadCleanBtn.setAttribute('data-base-href', cleanBase);
            downloadCleanBtn.href = `${cleanBase}?quality=${state.selectedQuality || '1080'}`;
        }

        // Reset cleanedVideo source
        if (cleanedVideo) {
            cleanedVideo.src = '';
            cleanedVideo.removeAttribute('src');
        }

        // Load source video URL: If Caption Add mode is active and Watermark Remove is active,
        // ALWAYS use the clean watermark-removed video so user previews and captions on top of clean video!
        let targetSrc = data.video_url;
        if (captionState.isCaptionAddActive) {
            if (captionState.isWatermarkRemoveActive && (state.cleanVideoUrl || state.serverCleanUrl)) {
                targetSrc = state.cleanVideoUrl || state.serverCleanUrl;
            } else if (!captionState.isWatermarkRemoveActive) {
                targetSrc = data.video_url;
            }
        } else {
            targetSrc = data.video_url;
        }
        sourceVideo.src = targetSrc;
        sourceVideo.muted = false;
        sourceVideo.volume = 1.0;
        if (previewVolIcon) previewVolIcon.classList.remove('hidden');
        if (previewMuteIcon) previewMuteIcon.classList.add('hidden');
        sourceVideo.load();

        applyAspectRatio(previewPlayerContainer, data.metadata);
        applyAspectRatio(cleanPlayerContainer, data.metadata);

        // Hide caption download card for fresh video
        if (captionDownloadCard) captionDownloadCard.classList.add('hidden');

        // Reset Right (After) to initial placeholder
        if (afterPlaceholder) afterPlaceholder.classList.remove('hidden');
        if (cleanVideoScreen) cleanVideoScreen.classList.add('hidden');
        if (externalControlBar) externalControlBar.classList.add('hidden');

        // Reset Center to State 1 (Remove Watermark Button & Quality & Arrow)
        if (removerInitialWrap) removerInitialWrap.classList.remove('hidden');
        if (centerActionsCompleted) centerActionsCompleted.classList.add('hidden');
        if (btnStartAutoProcess) {
            btnStartAutoProcess.disabled = false;
            btnStartAutoProcess.classList.remove('btn-success', 'is-processing');
        }
        if (removerInitialWrap) removerInitialWrap.classList.remove('is-processing');
        if (removerBtnText) removerBtnText.textContent = 'Remove Watermark';
        if (removerStatusSubtext) {
            removerStatusSubtext.innerHTML = '<span>⚡ Click to Remove Dola Watermark</span>';
        }

        if (previewSeeker) {
            previewSeeker.value = 0;
            previewSeeker.style.background = 'linear-gradient(to right, #00f2fe 0%, rgba(255,255,255,0.18) 0%)';
        }
        if (previewVideoScreen) previewVideoScreen.classList.remove('playing');
        if (previewPlayIcon) previewPlayIcon.classList.remove('hidden');
        if (previewPauseIcon) previewPauseIcon.classList.add('hidden');

        // Initialize AI speech transcription if caption add mode is active
        if (captionState.isCaptionAddActive) {
            if (data.transcription && data.transcription.has_speech && data.transcription.cues && data.transcription.cues.length > 0) {
                if (captionTextInput) captionTextInput.value = data.transcription.formatted_text;
                captionState.cues = data.transcription.cues;
                if (captionSpeechBadge) {
                    captionSpeechBadge.textContent = `🎙️ AI Speech Synced (${data.transcription.cues.length} lines)`;
                    captionSpeechBadge.classList.remove('hidden');
                }
                if (previewCaptionOverlay) previewCaptionOverlay.classList.remove('hidden');
                updateLiveSubtitleOverlay(0);
            } else {
                captionState.cues = [];
                // If video has audio, trigger background speech transcription asynchronously
                if (data.metadata && data.metadata.has_audio) {
                    if (captionSpeechBadge) {
                        captionSpeechBadge.textContent = '⏳ AI Transcribing voice in background...';
                        captionSpeechBadge.classList.remove('hidden');
                    }
                    if (captionTextInput) {
                        captionTextInput.placeholder = 'Transcribing spoken words from video... (or type your own)';
                    }
                    fetch('/api/transcribe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filename: data.filename })
                    })
                    .then(res => res.json())
                    .then(transData => {
                        if (transData.success && transData.has_speech && transData.cues && transData.cues.length > 0) {
                            if (captionTextInput && (!captionTextInput.value || captionTextInput.value.trim() === '')) {
                                captionTextInput.value = transData.formatted_text;
                            }
                            captionState.cues = transData.cues;
                            if (captionSpeechBadge) {
                                captionSpeechBadge.textContent = `🎙️ AI Speech Synced (${transData.cues.length} lines)`;
                                captionSpeechBadge.classList.remove('hidden');
                            }
                            if (previewCaptionOverlay) previewCaptionOverlay.classList.remove('hidden');
                            updateLiveSubtitleOverlay(sourceVideo ? sourceVideo.currentTime : 0);
                        } else {
                            if (captionSpeechBadge) {
                                captionSpeechBadge.textContent = '🔇 No Speech Detected (Video has no voice)';
                                captionSpeechBadge.classList.remove('hidden');
                            }
                        }
                    })
                    .catch(err => {
                        console.warn('Background transcription error:', err);
                        if (captionSpeechBadge) {
                            captionSpeechBadge.textContent = '🔇 Manual Subtitle Mode';
                            captionSpeechBadge.classList.remove('hidden');
                        }
                    });
                } else {
                    if (captionTextInput) {
                        captionTextInput.value = '';
                        captionTextInput.placeholder = 'No audio stream in this video. You can type custom subtitles here...';
                    }
                    if (captionSpeechBadge) {
                        captionSpeechBadge.textContent = '🔇 No Audio in Video';
                        captionSpeechBadge.classList.remove('hidden');
                    }
                    if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');
                    updateLiveSubtitleOverlay(0);
                }
            }
        } else {
            if (captionSpeechBadge) captionSpeechBadge.classList.add('hidden');
            if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');
            captionState.cues = [];
        }

        // Switch view
        if (heroSection) heroSection.classList.add('collapsed');
        uploadCard.classList.add('hidden');
        if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
        if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
        if (resultCard) resultCard.classList.add('hidden');
        previewActionCard.classList.remove('hidden');
        document.body.classList.add('studio-view-active');

        // Update UI based on active feature toggles (caption mode vs watermark only)
        updateFeatureTogglesUI();

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function initDefaultCaptionsForDuration(duration) {
        if (!captionState.cues || captionState.cues.length === 0) {
            if (captionTextInput && (!captionTextInput.value || captionTextInput.value.trim() === '')) {
                captionTextInput.placeholder = 'Type custom subtitles or load captions...';
            }
        }
    }

    function formatCueTimeSimple(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function returnToUpload() {
        if (sourceVideo) sourceVideo.pause();
        if (cleanedVideo) cleanedVideo.pause();
        state.hasUserProcessedWatermark = false;
        state.serverCleanUrl = null;
        state.cleanVideoUrl = null;
        state.currentFilename = null;
        if (cleanedVideo) {
            cleanedVideo.src = '';
            cleanedVideo.removeAttribute('src');
        }
        if (afterBufferingOverlay) afterBufferingOverlay.classList.add('hidden');
        if (cleanPlayerContainer) cleanPlayerContainer.classList.remove('has-buffering-active');
        if (afterPlaceholder) afterPlaceholder.classList.remove('hidden');
        if (cleanVideoScreen) cleanVideoScreen.classList.add('hidden');
        if (externalControlBar) externalControlBar.classList.add('hidden');
        if (removerInitialWrap) {
            removerInitialWrap.classList.remove('hidden');
            removerInitialWrap.classList.remove('is-processing');
        }
        if (centerActionsCompleted) centerActionsCompleted.classList.add('hidden');
        if (removerStatusSubtext) removerStatusSubtext.innerHTML = '<span>⚡ Click to Remove Dola Watermark</span>';
        if (btnStartAutoProcess) {
            btnStartAutoProcess.disabled = false;
            btnStartAutoProcess.classList.remove('is-processing');
        }
        if (removerBtnText) removerBtnText.textContent = 'Remove Watermark';
        previewActionCard.classList.add('hidden');
        if (resultCard) resultCard.classList.add('hidden');
        document.body.classList.remove('studio-view-active');

        if (state.isBulkStudioMode || currentMode === 'bulk') {
            if (state.currentBulkIndex != null && typeof bulkQueue !== 'undefined' && bulkQueue[state.currentBulkIndex] && bulkQueue[state.currentBulkIndex].hasUserEditedSubtitles) {
                bulkQueue[state.currentBulkIndex].customFormattedText = captionTextInput ? captionTextInput.value : '';
                bulkQueue[state.currentBulkIndex].customCues = parseSubtitlesText(bulkQueue[state.currentBulkIndex].customFormattedText, (state.videoMeta && state.videoMeta.duration) || 10);
            }
            state.isBulkStudioMode = false;
            currentMode = 'bulk';
            if (tabBulkMode) tabBulkMode.classList.add('active');
            if (tabSingleMode) tabSingleMode.classList.remove('active');
            if (btnBackText) btnBackText.textContent = 'Upload Another Video';
            if (bulkStudioBatchPill) bulkStudioBatchPill.classList.add('hidden');
            if (studioBulkFormatBar) studioBulkFormatBar.classList.add('hidden');
            if (videoInfoInline) videoInfoInline.classList.remove('hidden');
            if (btnCaptionEditText) btnCaptionEditText.textContent = '⬇ Download';
            
            if (uploadCard) uploadCard.classList.add('hidden');
            if (typeof bulkQueue !== 'undefined' && bulkQueue.length > 0) {
                if (bulkQueueCard) bulkQueueCard.classList.remove('hidden');
                if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
                if (heroSection) heroSection.classList.add('collapsed');
                renderBulkQueue();
            } else {
                if (bulkUploadCard) bulkUploadCard.classList.remove('hidden');
                if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
                if (heroSection) heroSection.classList.remove('collapsed');
            }
        } else {
            if (uploadCard) uploadCard.classList.remove('hidden');
            if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
            if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
            if (heroSection) heroSection.classList.remove('collapsed');
        }

        if (videoInput) videoInput.value = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    if (btnBackToUpload) btnBackToUpload.addEventListener('click', returnToUpload);
    if (btnClosePreview) btnClosePreview.addEventListener('click', returnToUpload);
    if (btnBackFromResult) btnBackFromResult.addEventListener('click', returnToUpload);
    if (btnCloseResult) btnCloseResult.addEventListener('click', returnToUpload);
    if (btnProcessAnother) btnProcessAnother.addEventListener('click', returnToUpload);

    // --- DOLA EDITS: FEATURE TOGGLES (WATERMARK REMOVE & CAPTION ADD) ---
    function updateFeatureTogglesUI() {
        if (toggleWatermark) {
            if (captionState.isWatermarkRemoveActive) {
                toggleWatermark.classList.add('active');
            } else {
                toggleWatermark.classList.remove('active');
            }
        }

        if (toggleCaption) {
            if (captionState.isCaptionAddActive) {
                toggleCaption.classList.add('active');
                if (captionStudioPanel) captionStudioPanel.classList.remove('hidden');
            } else {
                toggleCaption.classList.remove('active');
                if (captionStudioPanel) captionStudioPanel.classList.add('hidden');
            }
        }

        const watermarkStudioPanel = document.getElementById('watermarkStudioPanel');
        if (watermarkStudioPanel) watermarkStudioPanel.classList.add('hidden');

        // Apply Caption Mode vs Watermark Only Mode across UI
        if (captionState.isCaptionAddActive) {
            // Caption Add Mode (2-Column Studio: Clean Player Left + Subtitle Panel Right):
            if (studioColCenter) studioColCenter.classList.add('hidden');
            if (studioColAfter) studioColAfter.classList.add('hidden');
            if (comparisonStudioGrid) comparisonStudioGrid.classList.add('caption-studio-mode');
            if (previewActionCard) previewActionCard.classList.add('caption-mode-active');
            if (captionStudioPanel) captionStudioPanel.classList.remove('hidden');

            if (captionState.isWatermarkRemoveActive && (state.cleanVideoUrl || state.serverCleanUrl)) {
                if (beforePillDot) {
                    beforePillDot.classList.remove('dot-red');
                    beforePillDot.classList.add('dot-green');
                }
                if (beforePillLabel) beforePillLabel.textContent = 'Clean Video';
                if (beforePillBadge) beforePillBadge.textContent = '(Watermark Removed • Live Captions)';
            } else {
                if (beforePillDot) {
                    beforePillDot.classList.remove('dot-green');
                    beforePillDot.classList.add('dot-red');
                }
                if (beforePillLabel) beforePillLabel.textContent = 'Uploaded Video';
                if (beforePillBadge) beforePillBadge.textContent = '(Live Captions Only)';
            }
            if (previewCaptionOverlay && !state.isCurrentlyBurnedVideo) previewCaptionOverlay.classList.remove('hidden');

        } else {
            // Watermark Only Mode (Classic 3-Column Studio: Before | Remover / Download & Quality | After):
            if (captionStudioPanel) captionStudioPanel.classList.add('hidden');
            if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');
            if (comparisonStudioGrid) comparisonStudioGrid.classList.remove('caption-studio-mode');
            if (previewActionCard) previewActionCard.classList.remove('caption-mode-active');

            if (studioColCenter) studioColCenter.classList.remove('hidden');
            if (studioColAfter) studioColAfter.classList.remove('hidden');

            if (beforePillDot) {
                beforePillDot.classList.remove('dot-green');
                beforePillDot.classList.add('dot-red');
            }
            if (beforePillLabel) beforePillLabel.textContent = 'Before';
            if (beforePillBadge) beforePillBadge.textContent = '(Uploaded Video)';
            const beforePillElem = document.getElementById('beforeTitlePill');
            if (beforePillElem) beforePillElem.classList.remove('hidden');

            // If user has explicitly processed watermark in this session:
            if (state.hasUserProcessedWatermark) {
                if (removerInitialWrap) removerInitialWrap.classList.add('hidden');
                if (centerActionsCompleted) centerActionsCompleted.classList.remove('hidden');
                if (afterPlaceholder) afterPlaceholder.classList.add('hidden');
                if (cleanVideoScreen) cleanVideoScreen.classList.remove('hidden');
                if (externalControlBar) externalControlBar.classList.remove('hidden');
            } else {
                if (removerInitialWrap) removerInitialWrap.classList.remove('hidden');
                if (centerActionsCompleted) centerActionsCompleted.classList.add('hidden');
                if (afterPlaceholder) afterPlaceholder.classList.remove('hidden');
                if (cleanVideoScreen) cleanVideoScreen.classList.add('hidden');
                if (externalControlBar) externalControlBar.classList.add('hidden');
            }
        }

        // In display player, ensure appropriate video is loaded based on active mode
        let targetUrl = state.rawVideoUrl;
        if (captionState.isCaptionAddActive) {
            if (captionState.isWatermarkRemoveActive && (state.cleanVideoUrl || state.serverCleanUrl)) {
                targetUrl = state.cleanVideoUrl || state.serverCleanUrl;
            } else if (!captionState.isWatermarkRemoveActive) {
                targetUrl = state.rawVideoUrl;
            }
        } else if (!captionState.isCaptionAddActive) {
            // In watermark-only Before/After mode, Left column is Before (original video)
            targetUrl = state.rawVideoUrl;
        }
        if (targetUrl && sourceVideo) {
            if (!sourceVideo.src || !sourceVideo.src.endsWith(targetUrl)) {
                const curTime = sourceVideo.currentTime || 0;
                const wasPlaying = !sourceVideo.paused;
                sourceVideo.src = targetUrl;
                sourceVideo.currentTime = curTime;
                if (wasPlaying) sourceVideo.play().catch(() => {});
            }
        }

        // Trigger overlay update for current time
        if (sourceVideo && sourceVideo.currentTime !== undefined) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
        if (cleanedVideo && cleanedVideo.currentTime !== undefined) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
    }

    if (toggleWatermark) {
        toggleWatermark.addEventListener('click', () => {
            captionState.isWatermarkRemoveActive = !captionState.isWatermarkRemoveActive;
            updateFeatureTogglesUI();
        });
    }

    if (toggleCaption) {
        toggleCaption.addEventListener('click', () => {
            captionState.isCaptionAddActive = !captionState.isCaptionAddActive;
            updateFeatureTogglesUI();
            if (bulkQueue && bulkQueue.length > 0) {
                renderBulkQueue();
            }
        });
    }

    // --- SUBTITLE & CAPTION PARSER (SRT, VTT, TXT, NOTEGPT) ---
    function parseTimestamp(timeStr) {
        if (!timeStr) return 0;
        const m = String(timeStr).trim().match(/(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?/);
        if (!m) return null;
        const hours = +(m[1] || 0);
        const mins = +m[2];
        const secs = +m[3];
        const ms = m[4] ? +(m[4].padEnd(3, '0').slice(0, 3)) : 0;
        return hours * 3600 + mins * 60 + secs + ms / 1000;
    }

    function formatCueTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return "0:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 10);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}.${ms}`;
    }

    function parseSubtitlesText(rawText, durationOverride) {
        if (!rawText || !rawText.trim()) return [];
        const text = rawText.replace(/\r/g, '').trim();
        const duration = durationOverride || (state.videoMeta && state.videoMeta.duration) || 10;
        let cues = [];

        if (text.includes('-->')) {
            // SRT or VTT standard cue blocks
            const blocks = text.split(/\n{2,}/);
            for (const block of blocks) {
                const rawLines = block.split('\n').map(l => l.trim()).filter(l => l && l !== 'WEBVTT' && !/^\d+$/.test(l));
                const arrowLine = rawLines.find(l => l.includes('-->'));
                if (!arrowLine) continue;
                const times = arrowLine.match(/(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?/g);
                if (!times || times.length < 2) continue;
                const start = parseTimestamp(times[0]);
                const end = parseTimestamp(times[1]);
                let cueText = rawLines.filter(l => l !== arrowLine).join(' ').trim();
                cueText = cueText.replace(/^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\s*[-–—]|-->|to)\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[\]\)]?\s*[:\s-]*/i, '').trim();
                if (cueText && start !== null && end !== null && end > start) {
                    cues.push({ start, end, text: cueText });
                }
            }
        } else {
            // Timestamp formats:
            // 1. [0:00 - 0:03] Text or 0:00 - 0:03 Text or (0:00 - 0:03) Text
            const rangeRegex = /^\s*[\[\(]?\s*((?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\s*(?:[-–—]|-->|to)\s*((?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)[\]\)]?\s*[:\s-]*(.*)$/i;
            // 2. [0:02] Text or (0:02) Text
            const singleTimeRegex = /^\s*[\[\(]?\s*((?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)[\]\)]\s*[:\s-]*(.*)$/i;

            const lines = text.split('\n');
            let hasTimestamps = false;

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                if (!line) continue;

                let m = line.match(rangeRegex);
                if (m) {
                    hasTimestamps = true;
                    const start = parseTimestamp(m[1]);
                    const end = parseTimestamp(m[2]);
                    let cueText = m[3].trim();
                    cueText = cueText.replace(/^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[\]\)]?\s*[:\s-]*/i, '').trim();
                    if (cueText && start !== null && end !== null && end > start) {
                        cues.push({ start, end, text: cueText });
                    }
                    continue;
                }

                m = line.match(singleTimeRegex);
                if (m) {
                    hasTimestamps = true;
                    const start = parseTimestamp(m[1]);
                    let cueText = m[2].trim();
                    if (cueText && start !== null) {
                        cues.push({ start, end: start + 2.5, text: cueText });
                    }
                }
            }

            // If user did NOT supply timestamps, split duration evenly across non-empty lines!
            if (!hasTimestamps || cues.length === 0) {
                const nonBlankLines = lines.map(l => l.trim()).filter(l => l.length > 0);
                if (nonBlankLines.length > 0) {
                    const step = duration / nonBlankLines.length;
                    cues = nonBlankLines.map((lineText, idx) => {
                        let cleanText = lineText.replace(/^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\s*[-–—]|-->|to)\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[\]\)]?\s*[:\s-]*/i, '');
                        cleanText = cleanText.replace(/^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?[\]\)]?\s*[:\s-]*/i, '').trim();
                        return {
                            start: parseFloat((idx * step).toFixed(2)),
                            end: (idx === nonBlankLines.length - 1) ? parseFloat(duration.toFixed(2)) : parseFloat(((idx + 1) * step).toFixed(2)),
                            text: cleanText || lineText
                        };
                    });
                }
            } else {
                // Sort cues chronologically
                cues.sort((a, b) => a.start - b.start);

                // Only bridge tiny micro-gaps (< 0.4s) for smooth visual display.
                // Real silence pauses (>= 0.4s) are preserved so subtitles never display early before speech!
                for (let i = 0; i < cues.length - 1; i++) {
                    const gap = cues[i + 1].start - cues[i].end;
                    if (gap > 0 && gap < 0.4) {
                        cues[i].end = cues[i + 1].start;
                    }
                }
            }
        }
        return cues.sort((a, b) => a.start - b.start);
    }

    // Poller to detect when background watermark-clean completes
    function pollCleanVideoReady(filename) {
        const cleanName = `dolaedits_clean_${filename.replace(/\.[^/.]+$/, '')}.mp4`;
        const checkUrl = `/api/media/outputs/${cleanName}`;
        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            if (attempts > 20) { clearInterval(interval); return; }
            try {
                const resp = await fetch(checkUrl, { method: 'HEAD' });
                if (resp.ok) {
                    state.cleanVideoUrl = checkUrl;
                    clearInterval(interval);
                    // If player is currently in live preview and using rawVideoUrl, switch to clean video
                    if (!state.isCurrentlyBurnedVideo && sourceVideo && sourceVideo.src && sourceVideo.src.includes(state.rawVideoUrl)) {
                        const curTime = sourceVideo.currentTime || 0;
                        const wasPlaying = !sourceVideo.paused;
                        sourceVideo.src = checkUrl;
                        sourceVideo.currentTime = curTime;
                        if (wasPlaying) sourceVideo.play().catch(() => {});
                    }
                }
            } catch (e) {}
        }, 2000);
    }

    // Helper: If video currently playing is a burned video, switch back to clean video for live previewing tweaks
    function ensureLivePreviewMode() {
        const isBurnedPlaying = state.isCurrentlyBurnedVideo || 
            (state.burnedVideoUrl && sourceVideo && sourceVideo.src && sourceVideo.src.includes(state.burnedVideoUrl));
        if (isBurnedPlaying) {
            state.isCurrentlyBurnedVideo = false;
            state.burnedVideoUrl = null;
            const targetUrl = state.cleanVideoUrl || state.rawVideoUrl;
            if (targetUrl && sourceVideo) {
                const curTime = sourceVideo.currentTime || 0;
                const wasPlaying = !sourceVideo.paused;
                if (!sourceVideo.src.includes(targetUrl)) {
                    sourceVideo.src = targetUrl;
                    sourceVideo.currentTime = curTime;
                    if (wasPlaying) sourceVideo.play().catch(() => {});
                }
            }
            if (previewCaptionOverlay) previewCaptionOverlay.classList.remove('hidden');
        }
    }

    // Real-Time Caption Text Input Handler
    if (captionTextInput) {
        captionTextInput.addEventListener('focus', ensureLivePreviewMode);
        captionTextInput.addEventListener('input', (e) => {
            ensureLivePreviewMode();
            const raw = e.target.value;
            const duration = (state.videoMeta && state.videoMeta.duration) || 10;
            captionState.cues = parseSubtitlesText(raw, duration);
            if (state.isBulkStudioMode && state.currentBulkIndex != null && typeof bulkQueue !== 'undefined' && bulkQueue[state.currentBulkIndex]) {
                bulkQueue[state.currentBulkIndex].customCues = captionState.cues;
                bulkQueue[state.currentBulkIndex].customFormattedText = raw;
                bulkQueue[state.currentBulkIndex].hasUserEditedSubtitles = true;
            }
            if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
            if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
        });
    }

    // Style Chips Selector
    if (captionStyleChips) {
        const chips = captionStyleChips.querySelectorAll('.style-chip');
        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                ensureLivePreviewMode();
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                captionState.style = chip.dataset.style;
                if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
                if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
            });
        });
    }

    // Size Segmented Buttons
    if (captionSizeSeg) {
        const segBtns = captionSizeSeg.querySelectorAll('.seg-btn');
        segBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                ensureLivePreviewMode();
                segBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                captionState.size = btn.dataset.size;
                const sizeMap = { sm: 0.042, md: 0.052, lg: 0.064 };
                captionState.fontScale = sizeMap[captionState.size] || 0.052;
                if (captionFontScale) captionFontScale.value = captionState.fontScale;
                if (captionFontScaleVal) captionFontScaleVal.textContent = `${(captionState.fontScale * 100).toFixed(1)}%`;
                if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
                if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
            });
        });
    }

    // Font Scale Fine-Tune Slider
    if (captionFontScale) {
        captionFontScale.addEventListener('input', (e) => {
            ensureLivePreviewMode();
            captionState.fontScale = parseFloat(e.target.value);
            if (captionFontScaleVal) captionFontScaleVal.textContent = `${(captionState.fontScale * 100).toFixed(1)}%`;
            if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
            if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
        });
    }

    // Line Height Slider
    if (captionLineHeight) {
        captionLineHeight.addEventListener('input', (e) => {
            ensureLivePreviewMode();
            captionState.lineHeight = parseFloat(e.target.value);
            if (captionLineHeightVal) captionLineHeightVal.textContent = `${captionState.lineHeight.toFixed(2)}x`;
            if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
            if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
        });
    }

    // Position Y Slider (Bottom Margin)
    if (captionPosY) {
        captionPosY.addEventListener('input', (e) => {
            ensureLivePreviewMode();
            captionState.posY = parseFloat(e.target.value);
            if (captionPosYVal) captionPosYVal.textContent = `${Math.round(captionState.posY * 100)}%`;
            if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
            if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
        });
    }

    function updateLiveSubtitleOverlay(t = 0) {
        if (sourceVideo) updateLiveCaption(t || sourceVideo.currentTime || 0, sourceVideo);
        if (cleanedVideo) updateLiveCaption(t || cleanedVideo.currentTime || 0, cleanedVideo);
    }

    // Precise calculation of actual rendered video frame inside <video> (accounting for object-fit: contain letterbox & pillarbox)
    function getVideoRenderedRect(video) {
        if (!video) return { width: 240, height: 320, left: 0, top: 0, bottomOffset: 0 };
        const screen = video.parentElement;
        const vRect = video.getBoundingClientRect();
        const sRect = screen ? screen.getBoundingClientRect() : vRect;

        const vw = video.videoWidth || (state.videoMeta ? state.videoMeta.width : 720);
        const vh = video.videoHeight || (state.videoMeta ? state.videoMeta.height : 1280);

        if (!vw || !vh || !vRect.width || !vRect.height) {
            const w = sRect.width || 240;
            const h = sRect.height || 320;
            return { width: w, height: h, left: 0, top: 0, bottomOffset: 0 };
        }

        const vRatio = vw / vh;
        const eRatio = vRect.width / vRect.height;
        let rW, rH, rLeft, rTop;

        if (eRatio > vRatio) {
            // Container/video element is wider than actual video frame (pillarbox - black bars on left & right)
            rH = vRect.height;
            rW = rH * vRatio;
            rLeft = (vRect.left - sRect.left) + (vRect.width - rW) / 2;
            rTop = (vRect.top - sRect.top);
        } else {
            // Container/video element is taller than actual video frame (letterbox - black bars on top & bottom)
            rW = vRect.width;
            rH = rW / vRatio;
            rLeft = (vRect.left - sRect.left);
            rTop = (vRect.top - sRect.top) + (vRect.height - rH) / 2;
        }

        const bottomOffset = sRect.height - (rTop + rH);
        return {
            width: Math.max(80, rW),
            height: Math.max(80, rH),
            left: Math.max(0, rLeft),
            top: Math.max(0, rTop),
            bottomOffset: Math.max(0, bottomOffset)
        };
    }

    // Live Caption Overlay Sync Function
    function updateLiveCaption(currentTime, targetVideo) {
        const isClean = (targetVideo === cleanedVideo);
        const overlay = isClean ? cleanCaptionOverlay : previewCaptionOverlay;
        if (!overlay) return;

        // If the video currently playing is already burned with captions, NEVER show HTML overlay
        if (targetVideo === sourceVideo) {
            const isBurned = state.isCurrentlyBurnedVideo || 
                (state.burnedVideoUrl && sourceVideo.src && sourceVideo.src.includes(state.burnedVideoUrl));
            if (isBurned) {
                overlay.classList.add('hidden');
                return;
            }
        }

        if (!captionState.isCaptionAddActive || captionState.cues.length === 0) {
            overlay.classList.add('hidden');
            return;
        }

        let activeCue = captionState.cues.find(c => currentTime >= c.start && currentTime <= c.end);
        // When video is paused, show the nearest cue ONLY if we are very close to it (within 1 second)
        // This prevents showing wrong captions that don't match the visible frame's audio
        if (!activeCue && targetVideo.paused && captionState.cues.length > 0) {
            const nearestFuture = captionState.cues.find(c => c.start >= currentTime);
            const nearestPast = [...captionState.cues].reverse().find(c => c.end <= currentTime);
            // Show future cue only if it starts within 1 second
            if (nearestFuture && (nearestFuture.start - currentTime) < 1.0) {
                activeCue = nearestFuture;
            }
            // Or show past cue if it ended within 0.5 seconds ago
            else if (nearestPast && (currentTime - nearestPast.end) < 0.5) {
                activeCue = nearestPast;
            }
            // At time 0 (just loaded), show first cue as preview
            else if (currentTime < 0.3) {
                activeCue = captionState.cues[0];
            }
        }
        if (!activeCue || !activeCue.text || !activeCue.text.trim()) {
            overlay.classList.add('hidden');
            return;
        }

        let displayText = activeCue.text.trim();
        // Remove any bracketed or inline timestamp prefix if present
        displayText = displayText.replace(/^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\s*[-–—]|-->|to)\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[\]\)]?\s*[:\s-]*/i, '');
        displayText = displayText.replace(/^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?[\]\)]?\s*[:\s-]*/i, '').trim();

        if (!displayText) {
            overlay.classList.add('hidden');
            return;
        }

        const rect = getVideoRenderedRect(targetVideo);

        // Strictly constrain overlay to the exact rendered video rectangle (zero spill onto black bars)
        overlay.style.width = `${Math.round(rect.width)}px`;
        overlay.style.left = `${Math.round(rect.left)}px`;
        overlay.style.right = 'auto';
        overlay.style.maxWidth = `${Math.round(rect.width)}px`;

        const posYRatio = (captionState.posY !== undefined && captionState.posY !== null) ? captionState.posY : 0.07;
        const bottomPx = Math.round(rect.bottomOffset + (rect.height * posYRatio));
        overlay.style.bottom = `${bottomPx}px`;

        const textBox = overlay.querySelector('.caption-text-box');
        if (textBox) {
            textBox.textContent = displayText;
            textBox.style.lineHeight = captionState.lineHeight || 1.16;

            // Responsive font size proportional strictly to the actual rendered video width
            const scaleRatio = (captionState.fontScale || 0.052) / 0.052;
            let fontSize = Math.max(11, Math.round(rect.width * 0.066 * scaleRatio));
            textBox.style.fontSize = `${fontSize}px`;
            textBox.style.maxWidth = '90%';

            // ONE LINE CAPTION ENFORCEMENT:
            // Concise reel/shorts phrases (<= 5 words without explicit newline) must stay on a SINGLE line!
            const words = displayText.trim().split(/\s+/);
            const maxAllowedW = rect.width * 0.88;
            if (words.length <= 5 && !displayText.includes('\n')) {
                textBox.style.whiteSpace = 'nowrap';
            } else {
                textBox.style.whiteSpace = 'pre-wrap';
            }

            // Boundary safeguard: If text length exceeds 88% of actual video width, shrink font size to fit inside video
            if (textBox.scrollWidth > maxAllowedW) {
                fontSize = Math.max(10, Math.floor(fontSize * (maxAllowedW / textBox.scrollWidth)));
                textBox.style.fontSize = `${fontSize}px`;
            }
        }

        overlay.setAttribute('data-style', captionState.style || 'classic');
        overlay.classList.remove('hidden');
    }
    window.updateLiveCaption = updateLiveCaption;
    window.getVideoRenderedRect = getVideoRenderedRect;

    // AI Audio Speech Analysis on-demand trigger button
    if (btnAutoTranscribeVoice) {
        btnAutoTranscribeVoice.addEventListener('click', async () => {
            if (!state.currentFilename) {
                alert('Pehle video upload karein.');
                return;
            }
            const originalText = transcribeBtnLabel ? transcribeBtnLabel.innerHTML : '🤖 AI Detect Voice';
            if (transcribeBtnLabel) transcribeBtnLabel.innerHTML = `<span class="spinner-small"></span> Analyzing Voice...`;
            btnAutoTranscribeVoice.disabled = true;

            try {
                const resp = await fetch('/api/transcribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: state.currentFilename })
                });
                const res = await resp.json();
                if (res.success && res.has_speech && res.cues && res.cues.length > 0) {
                    if (captionTextInput) captionTextInput.value = res.formatted_text;
                    captionState.cues = res.cues;
                    ensureLivePreviewMode();
                    if (sourceVideo) updateLiveCaption(sourceVideo.currentTime, sourceVideo);
                    if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
                    if (captionSpeechBadge) {
                        captionSpeechBadge.textContent = `🎙️ AI Speech Synced (${res.cues.length} lines)`;
                        captionSpeechBadge.classList.remove('hidden');
                    }
                } else {
                    alert(res.message || 'Video audio me koi clear spoken voice detect nahi hui.');
                }
            } catch (err) {
                alert('Speech analysis error: ' + err.message);
            } finally {
                if (transcribeBtnLabel) transcribeBtnLabel.innerHTML = originalText;
                btnAutoTranscribeVoice.disabled = false;
            }
        });
    }

    // --- CORE PROCESS TRIGGER EXECUTOR (WATERMARK ONLY, CAPTION ONLY, OR COMBINED) ---
    async function executeProcessing({ remove_watermark, add_captions }) {
        if (!state.currentFilename) return;
        if (sourceVideo) sourceVideo.pause();

        if (btnStartAutoProcess) btnStartAutoProcess.disabled = true;
        if (btnCaptionRemoveOnlyWm) btnCaptionRemoveOnlyWm.disabled = true;
        if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = true;
        if (removerBtnText) removerBtnText.textContent = 'Processing...';

        if (previewActionCard) previewActionCard.classList.add('hidden');
        processingModal.classList.remove('hidden');
        const qName = (state.selectedQuality === '4k') ? '4K Ultra HD' : ((state.selectedQuality === '720') ? '720p HD' : ((state.selectedQuality === 'original') ? 'Original Quality' : '1080p FHD'));
        const titleMsg = (remove_watermark && add_captions) 
            ? `Dola Edits: Burning Captions & Preparing ${qName} Download...` 
            : add_captions ? `Dola Edits: Burning Captions (${qName})...` : `Dola Edits: Removing Watermark (${qName})...`;
        updateProgressUI(0, 0, state.videoMeta ? state.videoMeta.frame_count : 0, 0, '--', titleMsg);

        try {
            const resp = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: state.currentFilename,
                    remove_watermark: remove_watermark,
                    add_captions: add_captions,
                    captions: add_captions ? captionState.cues : [],
                    caption_style: captionState.style,
                    caption_size: captionState.fontScale,
                    caption_line_height: captionState.lineHeight,
                    caption_pos_y: captionState.posY,
                    quality: state.selectedQuality || '1080'
                })
            });

            let data;
            try {
                data = await resp.json();
            } catch (jsonErr) {
                const text = await resp.text().catch(() => '');
                throw new Error(text.slice(0, 120) || `Server error (${resp.status})`);
            }
            if (!resp.ok || !data.success) {
                throw new Error(data.error || 'Failed to start processing');
            }

            state.activeTaskId = data.task_id;
            startProgressPolling(data.task_id);
        } catch (err) {
            processingModal.classList.add('hidden');
            if (previewActionCard) previewActionCard.classList.remove('hidden');
            if (btnStartAutoProcess) btnStartAutoProcess.disabled = false;
            if (btnCaptionRemoveOnlyWm) btnCaptionRemoveOnlyWm.disabled = false;
            if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = false;
            if (removerBtnText) removerBtnText.textContent = 'Remover';
            alert('Processing error: ' + err.message);
        }
    }

    // 1. Center button: respects whatever toggles are currently ticked
    if (btnStartAutoProcess) {
        btnStartAutoProcess.addEventListener('click', () => {
            const doWm = captionState.isWatermarkRemoveActive;
            const duration = (state.videoMeta && state.videoMeta.duration) || 10;
            if (captionTextInput && captionTextInput.value.trim() && captionState.cues.length === 0) {
                captionState.cues = parseSubtitlesText(captionTextInput.value.trim(), duration);
            }
            const doCap = captionState.isCaptionAddActive && captionState.cues.length > 0;
            if (!doWm && !doCap) {
                alert('Please tick at least one option: "Watermark Remove" or "Caption Add".');
                return;
            }

            const chosenQ = state.selectedQuality || '1080';

            // SINGLE VIDEO WATERMARK-ONLY MODE:
            // As requested by user: "remove watermark pe click kre to sa nahi dena hai img 1 jaisa nai dena sirf after vala video screen he vaha buffering vala theam lagana hai aur koi details text nahi laagana"
            if (doWm && !doCap) {
                btnStartAutoProcess.disabled = true;
                btnStartAutoProcess.classList.add('is-processing');
                if (removerInitialWrap) removerInitialWrap.classList.add('is-processing');
                if (removerBtnText) removerBtnText.textContent = 'Removing Watermark...';

                if (removerStatusSubtext) {
                    removerStatusSubtext.innerHTML = `
                        <div class="remover-active-flow">
                            <div class="processing-glow-line"><div class="processing-glow-bar"></div></div>
                            <div class="processing-sub-hint">
                                <span class="hint-live-dot"></span>
                                <span>AI Inpainting in Progress</span>
                            </div>
                        </div>
                    `;
                }

                // Activate buffering theme on AFTER video screen only (Zero modal, zero text details)
                if (afterPlaceholder) afterPlaceholder.classList.add('hidden');
                if (afterBufferingOverlay) afterBufferingOverlay.classList.remove('hidden');
                if (cleanPlayerContainer) cleanPlayerContainer.classList.add('has-buffering-active');
                if (cleanVideoScreen) cleanVideoScreen.classList.add('hidden');

                // Case A: Server already has pre-cleaned video cached
                if (state.serverCleanUrl && (chosenQ === '1080' || chosenQ === 'original')) {
                    setTimeout(() => {
                        if (afterBufferingOverlay) afterBufferingOverlay.classList.add('hidden');
                        if (cleanPlayerContainer) cleanPlayerContainer.classList.remove('has-buffering-active');
                        state.hasUserProcessedWatermark = true;
                        state.cleanVideoUrl = state.serverCleanUrl;
                        if (cleanedVideo) {
                            cleanedVideo.src = `${state.serverCleanUrl}?t=${Date.now()}`;
                            cleanedVideo.load();
                        }
                        if (afterPlaceholder) afterPlaceholder.classList.add('hidden');
                        if (cleanVideoScreen) cleanVideoScreen.classList.remove('hidden');
                        if (externalControlBar) externalControlBar.classList.remove('hidden');
                        if (removerInitialWrap) removerInitialWrap.classList.add('hidden');
                        if (centerActionsCompleted) centerActionsCompleted.classList.remove('hidden');

                        if (downloadCleanBtn) {
                            const cleanBase = `/api/download-clean/${state.currentFilename}`;
                            downloadCleanBtn.setAttribute('data-base-href', cleanBase);
                            downloadCleanBtn.href = `${cleanBase}?quality=${chosenQ}`;
                        }

                        applyAspectRatio(previewPlayerContainer, state.videoMeta);
                        applyAspectRatio(cleanPlayerContainer, state.videoMeta);

                        btnStartAutoProcess.disabled = false;
                        btnStartAutoProcess.classList.remove('is-processing');
                        if (removerInitialWrap) removerInitialWrap.classList.remove('is-processing');
                        if (removerBtnText) removerBtnText.textContent = 'Remove Watermark';
                        if (removerStatusSubtext) removerStatusSubtext.innerHTML = '<span>⚡ Click to Remove Dola Watermark</span>';
                    }, 1200);
                    return;
                }

                // Case B: Background render needed (e.g. 720p or 4K) -> In-place processing without processingModal!
                executeProcessingInPlace({ remove_watermark: true, add_captions: false, quality: chosenQ });
                return;
            }

            executeProcessing({ remove_watermark: doWm, add_captions: doCap });
        });
    }

    // In-Place processing specifically for Watermark-Only mode (keeps studio view open with buffering theme on AFTER screen)
    async function executeProcessingInPlace({ remove_watermark, add_captions, quality }) {
        if (!state.currentFilename) return;
        if (sourceVideo) sourceVideo.pause();

        btnStartAutoProcess.disabled = true;
        btnStartAutoProcess.classList.add('is-processing');
        if (removerInitialWrap) removerInitialWrap.classList.add('is-processing');
        if (removerBtnText) removerBtnText.textContent = 'Removing Watermark...';

        if (removerStatusSubtext) {
            removerStatusSubtext.innerHTML = `
                <div class="remover-active-flow">
                    <div class="processing-glow-line"><div class="processing-glow-bar"></div></div>
                    <div class="processing-sub-hint">
                        <span class="hint-live-dot"></span>
                        <span>AI Inpainting in Progress</span>
                    </div>
                </div>
            `;
        }

        if (afterPlaceholder) afterPlaceholder.classList.add('hidden');
        if (afterBufferingOverlay) afterBufferingOverlay.classList.remove('hidden');
        if (cleanPlayerContainer) cleanPlayerContainer.classList.add('has-buffering-active');
        if (cleanVideoScreen) cleanVideoScreen.classList.add('hidden');

        try {
            const resp = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: state.currentFilename,
                    remove_watermark: remove_watermark,
                    add_captions: add_captions,
                    captions: [],
                    quality: quality || state.selectedQuality || '1080'
                })
            });

            let data;
            try {
                data = await resp.json();
            } catch (jsonErr) {
                const text = await resp.text().catch(() => '');
                throw new Error(text.slice(0, 120) || `Server error (${resp.status})`);
            }
            if (!resp.ok || !data.success) {
                throw new Error(data.error || 'Failed to start watermark removal');
            }

            state.activeTaskId = data.task_id;
            startInPlaceProgressPolling(data.task_id);
        } catch (err) {
            if (afterBufferingOverlay) afterBufferingOverlay.classList.add('hidden');
            if (cleanPlayerContainer) cleanPlayerContainer.classList.remove('has-buffering-active');
            if (afterPlaceholder) afterPlaceholder.classList.remove('hidden');
            btnStartAutoProcess.disabled = false;
            btnStartAutoProcess.classList.remove('is-processing');
            if (removerInitialWrap) removerInitialWrap.classList.remove('is-processing');
            if (removerBtnText) removerBtnText.textContent = 'Remove Watermark';
            if (removerStatusSubtext) removerStatusSubtext.innerHTML = '<span>⚡ Click to Remove Dola Watermark</span>';
            alert('Processing error: ' + err.message);
        }
    }

    function startInPlaceProgressPolling(taskId) {
        if (state.pollInterval) clearInterval(state.pollInterval);
        state.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/status/${taskId}`);
                if (!resp.ok) return;

                const task = await resp.json();
                if (task.status === 'completed') {
                    clearInterval(state.pollInterval);
                    if (afterBufferingOverlay) afterBufferingOverlay.classList.add('hidden');
                    if (cleanPlayerContainer) cleanPlayerContainer.classList.remove('has-buffering-active');
                    showResultScreen(task);
                } else if (task.status === 'error') {
                    clearInterval(state.pollInterval);
                    if (afterBufferingOverlay) afterBufferingOverlay.classList.add('hidden');
                    if (cleanPlayerContainer) cleanPlayerContainer.classList.remove('has-buffering-active');
                    if (afterPlaceholder) afterPlaceholder.classList.remove('hidden');
                    btnStartAutoProcess.disabled = false;
                    btnStartAutoProcess.classList.remove('is-processing');
                    if (removerInitialWrap) removerInitialWrap.classList.remove('is-processing');
                    if (removerBtnText) removerBtnText.textContent = 'Remove Watermark';
                    if (removerStatusSubtext) removerStatusSubtext.innerHTML = '<span>⚡ Click to Remove Dola Watermark</span>';
                    alert('Watermark removal error: ' + (task.error || 'Unknown error'));
                }
            } catch (err) {
                console.warn('In-place status check warning:', err);
            }
        }, 500);
    }

    // 2. Caption Section Option 1: "Download Clean Video"
    if (btnCaptionRemoveOnlyWm) {
        btnCaptionRemoveOnlyWm.addEventListener('click', () => {
            if (state.cleanVideoUrl) {
                const a = document.createElement('a');
                a.href = state.cleanVideoUrl;
                a.download = `dolaedits_clean_${state.currentFilename ? state.currentFilename.replace(/\.[^/.]+$/, '') : 'video'}.mp4`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } else {
                executeProcessing({ remove_watermark: true, add_captions: false });
            }
        });
    }

    // 3. Caption Section: "⬇ Download (Apply Captions, Render & Download Video)"
    if (btnCaptionEditCombined) {
        btnCaptionEditCombined.addEventListener('click', () => {
            if (state.isBulkStudioMode) {
                executeBulkStudioBatchProcessing();
                return;
            }

            const duration = (state.videoMeta && state.videoMeta.duration) || 10;
            if (captionTextInput && captionTextInput.value.trim()) {
                captionState.cues = parseSubtitlesText(captionTextInput.value.trim(), duration);
            }
            if (captionState.cues.length === 0) {
                alert('Please enter caption text in the box above before downloading.');
                if (captionTextInput) captionTextInput.focus();
                return;
            }

            // If video is already rendered with current captions, trigger immediate download!
            if (state.isCurrentlyBurnedVideo && state.activeTaskId) {
                const q = state.selectedQuality || '1080';
                const a = document.createElement('a');
                a.href = `/api/download/${state.activeTaskId}?quality=${q}`;
                a.download = `dolaedits_${q}_${state.activeTaskId.slice(0, 6)}.mp4`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                return;
            }

            // Mark flag to automatically download as soon as processing completes!
            state.autoTriggerDownload = true;
            executeProcessing({ 
                remove_watermark: captionState.isWatermarkRemoveActive, 
                add_captions: true 
            });
        });
    }

    function startProgressPolling(taskId) {
        if (state.pollInterval) clearInterval(state.pollInterval);
        const processStartTime = Date.now();
        if (statElapsed) statElapsed.textContent = '00:00';
        if (processBufferingBadgeText) processBufferingBadgeText.textContent = '⚡ Buffering & AI Processing...';

        state.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/status/${taskId}`);
                if (!resp.ok) return;

                const task = await resp.json();

                // Live Elapsed Time calculation
                const elapsedSec = Math.floor((Date.now() - processStartTime) / 1000);
                const elapsedMins = Math.floor(elapsedSec / 60);
                const elapsedRemSec = elapsedSec % 60;
                const elapsedStr = `${elapsedMins < 10 ? '0' : ''}${elapsedMins}:${elapsedRemSec < 10 ? '0' : ''}${elapsedRemSec}`;
                if (statElapsed) statElapsed.textContent = elapsedStr;

                if (task.status === 'processing') {
                    let etaText = '--';
                    if (task.eta && task.eta > 0) {
                        etaText = `${Math.ceil(task.eta)}s`;
                    } else if (task.fps > 0 && task.total_frames > task.current_frame) {
                        const remFrames = task.total_frames - task.current_frame;
                        const calcSec = Math.ceil(remFrames / task.fps);
                        etaText = calcSec > 0 ? `${calcSec}s` : 'Finishing...';
                    } else if (task.percent >= 90) {
                        etaText = 'Finishing...';
                    } else {
                        etaText = '~12s';
                    }

                    if (processBufferingBadgeText) {
                        processBufferingBadgeText.textContent = task.percent >= 90 ? '⚡ Buffering & Finalizing Audio...' : '⚡ Buffering & AI Processing...';
                    }
                    updateProgressUI(
                        task.percent,
                        task.current_frame,
                        task.total_frames,
                        task.fps,
                        etaText,
                        task.percent >= 90 ? 'Finalizing audio & video master...' : 'Permanently eliminating Dola watermark...'
                    );
                } else if (task.status === 'completed') {
                    clearInterval(state.pollInterval);
                    if (processBufferingBadgeText) processBufferingBadgeText.textContent = '🎉 Complete!';
                    updateProgressUI(100, task.total_frames, task.total_frames, task.fps, 'Done!', 'Complete! Loading clean video...');

                    setTimeout(() => {
                        processingModal.classList.add('hidden');
                        if (previewActionCard) previewActionCard.classList.remove('hidden');
                        showResultScreen(task);
                    }, 400);
                } else if (task.status === 'error') {
                    clearInterval(state.pollInterval);
                    processingModal.classList.add('hidden');
                    if (previewActionCard) previewActionCard.classList.remove('hidden');
                    if (btnStartAutoProcess) btnStartAutoProcess.disabled = false;
                    if (removerBtnText) removerBtnText.textContent = 'Remover';
                    alert('Error during video processing: ' + (task.error || 'Unknown error'));
                }
            } catch (e) {
                console.error('Polling error:', e);
            }
        }, 350);
    }

    function updateProgressUI(pct, cur, total, fps, eta, statusMsg) {
        progressPercent.textContent = `${pct}%`;
        
        const circumference = 2 * Math.PI * 42;
        const offset = circumference - (pct / 100) * circumference;
        progressCircle.style.strokeDashoffset = offset;

        linearFill.style.width = `${pct}%`;
        statFrames.textContent = `${cur} / ${total}`;
        statFps.textContent = `${fps} fps`;
        statEta.textContent = eta;
        processingStatusText.textContent = statusMsg;
    }

    function showResultScreen(task) {
        if (btnStartAutoProcess) {
            btnStartAutoProcess.disabled = false;
            btnStartAutoProcess.classList.remove('is-processing');
        }
        if (removerInitialWrap) removerInitialWrap.classList.remove('is-processing');
        if (btnCaptionRemoveOnlyWm) btnCaptionRemoveOnlyWm.disabled = false;
        if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = false;
        if (removerBtnText) removerBtnText.textContent = 'Remove Watermark';
        if (removerStatusSubtext) removerStatusSubtext.innerHTML = '<span>⚡ Click to Remove Dola Watermark</span>';

        state.hasUserProcessedWatermark = true;
        state.cleanVideoUrl = task.video_url;

        // Load clean/rendered video into Right (After) screen
        cleanedVideo.src = `${task.video_url}?t=${Date.now()}`;
        cleanedVideo.load();
        if (downloadCleanBtn) {
            const baseClean = task.download_url || `/api/download/${task.task_id || state.activeTaskId}`;
            downloadCleanBtn.setAttribute('data-base-href', baseClean);
            downloadCleanBtn.href = `${baseClean}?quality=${state.selectedQuality || '1080'}`;
        }

        // If Caption Add mode is active:
        if (captionState.isCaptionAddActive) {
            state.isCurrentlyBurnedVideo = true;
            state.burnedVideoUrl = task.video_url;
            // Load rendered video directly into the active Studio player!
            if (sourceVideo) {
                sourceVideo.src = `${task.video_url}?t=${Date.now()}`;
                sourceVideo.load();
                sourceVideo.play().catch(() => {});
            }
            // Hide live overlay since captions are now burned into the video
            if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');

            // Automatically trigger download directly into browser
            const q = state.selectedQuality || '1080';
            const dlUrl = `${task.download_url}?quality=${q}`;
            const a = document.createElement('a');
            a.href = dlUrl;
            a.download = `dolaedits_${q}_${(task.task_id || state.activeTaskId || 'video').slice(0, 6)}.mp4`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            state.autoTriggerDownload = false;
            return;
        }

        // Watermark Only mode: reveal After video and controls
        if (afterBufferingOverlay) afterBufferingOverlay.classList.add('hidden');
        if (cleanPlayerContainer) cleanPlayerContainer.classList.remove('has-buffering-active');
        if (afterPlaceholder) afterPlaceholder.classList.add('hidden');
        if (cleanVideoScreen) cleanVideoScreen.classList.remove('hidden');
        if (externalControlBar) externalControlBar.classList.remove('hidden');

        // Transition Center to State 2 (Completed: Download & Upload Another)
        if (removerInitialWrap) removerInitialWrap.classList.add('hidden');
        if (centerActionsCompleted) centerActionsCompleted.classList.remove('hidden');

        // Ensure Left and Right containers have 100% identical aspect ratio classes
        applyAspectRatio(previewPlayerContainer, state.videoMeta);
        applyAspectRatio(cleanPlayerContainer, state.videoMeta);

        // Reset player UI
        if (videoSeeker) {
            videoSeeker.value = 0;
            videoSeeker.style.background = 'linear-gradient(to right, #00f2fe 0%, rgba(255,255,255,0.18) 0%)';
        }
        if (cleanVideoScreen) cleanVideoScreen.classList.remove('playing');
        if (playIcon) playIcon.classList.remove('hidden');
        if (pauseIcon) pauseIcon.classList.add('hidden');

        if (heroSection) heroSection.classList.add('collapsed');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // --- QUALITY SELECTION & AI ENHANCEMENT HANDLER ---
    const QUALITY_LABELS = {
        'original': 'Original Quality',
        '720': '720p HD',
        '1080': '1080p FHD',
        '4k': '4K Ultra HD'
    };

    function setVideoQuality(newQuality) {
        state.selectedQuality = newQuality;
        bulkChosenQuality = newQuality;
        const badgeLabel = QUALITY_LABELS[newQuality] || `${newQuality}p`;

        if (cleanQualityBadge) cleanQualityBadge.textContent = badgeLabel;
        if (captionQualityBadge) captionQualityBadge.textContent = badgeLabel;
        if (actionExportQualityBadge) actionExportQualityBadge.textContent = badgeLabel;
        const wmExportQualityBadge = document.getElementById('wmExportQualityBadge');
        if (wmExportQualityBadge) wmExportQualityBadge.textContent = badgeLabel;
        const bulkQueueQualityBadge = document.getElementById('bulkQueueQualityBadge');
        if (bulkQueueQualityBadge) bulkQueueQualityBadge.textContent = badgeLabel;

        // Sync all chip buttons active states across all boxes
        document.querySelectorAll('.quality-chip').forEach(chip => {
            if (chip.getAttribute('data-quality') === newQuality) {
                chip.classList.add('active');
            } else {
                chip.classList.remove('active');
            }
        });

        // Update download URLs with current quality parameter
        updateDownloadHref(downloadCleanBtn);
        updateDownloadHref(btnCaptionDownloadLink);
    }

    function updateDownloadHref(btn) {
        if (!btn) return;
        let base = btn.getAttribute('data-base-href');
        if (!base) {
            const currentHref = btn.getAttribute('href');
            if (currentHref && currentHref !== '#' && !currentHref.startsWith('javascript:')) {
                base = currentHref.split('?')[0];
                btn.setAttribute('data-base-href', base);
            }
        }
        if (base && base !== '#' && !base.startsWith('javascript:')) {
            const q = state.selectedQuality || '1080';
            btn.href = `${base}?quality=${q}`;
        }
    }

    // Attach click listeners to all quality chips (with delegation)
    document.addEventListener('click', (e) => {
        const chip = e.target.closest('.quality-chip');
        if (chip) {
            e.preventDefault();
            const q = chip.getAttribute('data-quality');
            if (q) {
                setVideoQuality(q);
            }
        }
    });

    // Provide immediate visual feedback on download button click
    function attachDownloadFeedback(btn) {
        if (!btn) return;
        btn.addEventListener('click', () => {
            const currentQuality = state.selectedQuality || '1080';
            const qualityName = QUALITY_LABELS[currentQuality] || 'HD';
            const originalHtml = btn.innerHTML;
            btn.style.pointerEvents = 'none';
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" style="animation: spin 0.8s linear infinite; vertical-align: middle; margin-right: 6px;">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
                </svg>
                <span>Enhancing to ${qualityName}...</span>
            `;
            setTimeout(() => {
                btn.innerHTML = originalHtml;
                btn.style.pointerEvents = '';
            }, 3000);
        });
    }
    attachDownloadFeedback(downloadCleanBtn);
    attachDownloadFeedback(btnCaptionDownloadLink);

    // --- EXTERNAL CUSTOM VIDEO PLAYER CONTROLS (STRICTLY BELOW VIDEO) ---
    function formatTime(seconds) {
        if (isNaN(seconds) || seconds <= 0) return "0:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function updateSeekerProgress() {
        if (!cleanedVideo.duration) return;
        const pct = (cleanedVideo.currentTime / cleanedVideo.duration) * 100;
        videoSeeker.value = pct;
        videoSeeker.style.background = `linear-gradient(to right, #00f2fe ${pct}%, rgba(255,255,255,0.18) ${pct}%)`;
        timeDisplay.textContent = `${formatTime(cleanedVideo.currentTime)} / ${formatTime(cleanedVideo.duration)}`;
        updateLiveCaption(cleanedVideo.currentTime, cleanedVideo);
    }

    function togglePlay() {
        if (cleanedVideo.paused || cleanedVideo.ended) {
            cleanedVideo.play();
        } else {
            cleanedVideo.pause();
        }
    }

    if (cleanVideoScreen) {
        cleanVideoScreen.addEventListener('click', togglePlay);
    }
    if (btnPlayPause) {
        btnPlayPause.addEventListener('click', togglePlay);
    }

    cleanedVideo.addEventListener('play', () => {
        cleanVideoScreen.classList.add('playing');
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
    });

    cleanedVideo.addEventListener('pause', () => {
        cleanVideoScreen.classList.remove('playing');
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    });

    cleanedVideo.addEventListener('ended', () => {
        cleanVideoScreen.classList.remove('playing');
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    });

    cleanedVideo.addEventListener('timeupdate', updateSeekerProgress);

    cleanedVideo.addEventListener('loadedmetadata', () => {
        videoSeeker.value = 0;
        videoSeeker.style.background = `linear-gradient(to right, #00f2fe 0%, rgba(255,255,255,0.18) 0%)`;
        timeDisplay.textContent = `0:00 / ${formatTime(cleanedVideo.duration)}`;
        updateLiveCaption(0, cleanedVideo);
    });

    // Scrub video timeline forward / backward ("video aage pichhe karne ki line")
    videoSeeker.addEventListener('input', (e) => {
        if (!cleanedVideo.duration) return;
        const pct = parseFloat(e.target.value);
        const targetTime = (pct / 100) * cleanedVideo.duration;
        cleanedVideo.currentTime = targetTime;
        videoSeeker.style.background = `linear-gradient(to right, #00f2fe ${pct}%, rgba(255,255,255,0.18) ${pct}%)`;
        timeDisplay.textContent = `${formatTime(targetTime)} / ${formatTime(cleanedVideo.duration)}`;
        updateLiveCaption(targetTime, cleanedVideo);
    });

    // Mute / Unmute
    if (btnMute) {
        btnMute.addEventListener('click', () => {
            cleanedVideo.muted = !cleanedVideo.muted;
            if (cleanedVideo.muted) {
                volIcon.classList.add('hidden');
                muteIcon.classList.remove('hidden');
            } else {
                volIcon.classList.remove('hidden');
                muteIcon.classList.add('hidden');
            }
        });
    }

    // (Fullscreen handled in unified toggle section at end of file)

    // --- PREVIEW VIDEO PLAYER CONTROLS (STRICTLY BELOW PREVIEW VIDEO) ---
    function updatePreviewSeekerProgress() {
        if (!sourceVideo.duration) return;
        const pct = (sourceVideo.currentTime / sourceVideo.duration) * 100;
        previewSeeker.value = pct;
        previewSeeker.style.background = `linear-gradient(to right, #00f2fe ${pct}%, rgba(255,255,255,0.18) ${pct}%)`;
        previewTimeDisplay.textContent = `${formatTime(sourceVideo.currentTime)} / ${formatTime(sourceVideo.duration)}`;
        updateLiveCaption(sourceVideo.currentTime, sourceVideo);
    }

    function togglePreviewPlay() {
        if (sourceVideo.paused || sourceVideo.ended) {
            sourceVideo.muted = false;
            sourceVideo.play().catch(() => {});
        } else {
            sourceVideo.pause();
        }
    }

    if (previewVideoScreen) {
        previewVideoScreen.addEventListener('click', togglePreviewPlay);
    }
    if (btnPreviewPlayPause) {
        btnPreviewPlayPause.addEventListener('click', togglePreviewPlay);
    }

    sourceVideo.addEventListener('play', () => {
        if (previewVideoScreen) previewVideoScreen.classList.add('playing');
        if (previewPlayIcon) previewPlayIcon.classList.add('hidden');
        if (previewPauseIcon) previewPauseIcon.classList.remove('hidden');
    });

    sourceVideo.addEventListener('pause', () => {
        if (previewVideoScreen) previewVideoScreen.classList.remove('playing');
        if (previewPlayIcon) previewPlayIcon.classList.remove('hidden');
        if (previewPauseIcon) previewPauseIcon.classList.add('hidden');
    });

    sourceVideo.addEventListener('ended', () => {
        if (previewVideoScreen) previewVideoScreen.classList.remove('playing');
        if (previewPlayIcon) previewPlayIcon.classList.remove('hidden');
        if (previewPauseIcon) previewPauseIcon.classList.add('hidden');
    });

    sourceVideo.addEventListener('timeupdate', updatePreviewSeekerProgress);

    sourceVideo.addEventListener('loadedmetadata', () => {
        if (previewSeeker) {
            previewSeeker.value = 0;
            previewSeeker.style.background = `linear-gradient(to right, #00f2fe 0%, rgba(255,255,255,0.18) 0%)`;
        }
        if (previewTimeDisplay) {
            previewTimeDisplay.textContent = `0:00 / ${formatTime(sourceVideo.duration)}`;
        }
        updateLiveCaption(0, sourceVideo);
    });

    sourceVideo.addEventListener('error', (e) => {
        console.warn('sourceVideo playback error encountered, falling back to rawVideoUrl:', state.rawVideoUrl);
        if (state.rawVideoUrl && (!sourceVideo.src || !sourceVideo.src.endsWith(state.rawVideoUrl))) {
            sourceVideo.src = state.rawVideoUrl;
            sourceVideo.load();
            sourceVideo.play().catch(() => {});
        }
    });

    // Scrub preview video timeline forward / backward ("video aage pichhe karne ki line")
    if (previewSeeker) {
        previewSeeker.addEventListener('input', (e) => {
            if (!sourceVideo.duration) return;
            const pct = parseFloat(e.target.value);
            const targetTime = (pct / 100) * sourceVideo.duration;
            sourceVideo.currentTime = targetTime;
            previewSeeker.style.background = `linear-gradient(to right, #00f2fe ${pct}%, rgba(255,255,255,0.18) ${pct}%)`;
            if (previewTimeDisplay) {
                previewTimeDisplay.textContent = `${formatTime(targetTime)} / ${formatTime(sourceVideo.duration)}`;
            }
            updateLiveCaption(targetTime, sourceVideo);
        });
    }

    // Preview Mute / Unmute
    if (btnPreviewMute) {
        btnPreviewMute.addEventListener('click', () => {
            sourceVideo.muted = !sourceVideo.muted;
            if (sourceVideo.muted) {
                previewVolIcon.classList.add('hidden');
                previewMuteIcon.classList.remove('hidden');
            } else {
                previewVolIcon.classList.remove('hidden');
                previewMuteIcon.classList.add('hidden');
            }
        });
    }

    // ==========================================
    // UNIFIED FULLSCREEN THEATRE MODE HANDLER
    // ==========================================
    let fsIdleTimeout = null;
    function resetFsIdleTimer(container) {
        if (!container) return;
        container.classList.remove('hide-fs-controls');
        clearTimeout(fsIdleTimeout);
        if (document.fullscreenElement) {
            fsIdleTimeout = setTimeout(() => {
                const vid = container.querySelector('video');
                if (vid && !vid.paused && !vid.ended && document.fullscreenElement) {
                    container.classList.add('hide-fs-controls');
                }
            }, 2800);
        }
    }

    [previewPlayerContainer, cleanPlayerContainer].forEach(container => {
        if (!container) return;
        container.addEventListener('mousemove', () => resetFsIdleTimer(container));
        container.addEventListener('touchstart', () => resetFsIdleTimer(container));
        container.addEventListener('click', () => resetFsIdleTimer(container));
    });

    document.addEventListener('fullscreenchange', () => {
        const isFsPreview = document.fullscreenElement === previewPlayerContainer;
        const isFsClean = document.fullscreenElement === cleanPlayerContainer;

        if (previewPlayerContainer) {
            previewPlayerContainer.classList.toggle('is-fullscreen', isFsPreview);
            if (!isFsPreview) previewPlayerContainer.classList.remove('hide-fs-controls');
        }
        if (cleanPlayerContainer) {
            cleanPlayerContainer.classList.toggle('is-fullscreen', isFsClean);
            if (!isFsClean) cleanPlayerContainer.classList.remove('hide-fs-controls');
        }

        if (previewFsEnterIcon && previewFsExitIcon) {
            if (isFsPreview) {
                previewFsEnterIcon.classList.add('hidden');
                previewFsExitIcon.classList.remove('hidden');
            } else {
                previewFsEnterIcon.classList.remove('hidden');
                previewFsExitIcon.classList.add('hidden');
            }
        }

        if (fsEnterIcon && fsExitIcon) {
            if (isFsClean) {
                fsEnterIcon.classList.add('hidden');
                fsExitIcon.classList.remove('hidden');
            } else {
                fsEnterIcon.classList.remove('hidden');
                fsExitIcon.classList.add('hidden');
            }
        }

        setTimeout(() => {
            if (sourceVideo) updateLiveCaption(sourceVideo.currentTime || 0, sourceVideo);
            if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime || 0, cleanedVideo);
        }, 60);
    });

    window.addEventListener('resize', () => {
        if (sourceVideo) updateLiveCaption(sourceVideo.currentTime || 0, sourceVideo);
        if (cleanedVideo) updateLiveCaption(cleanedVideo.currentTime || 0, cleanedVideo);
    });

    function toggleContainerFullscreen(container, fallbackVideo) {
        if (!document.fullscreenElement) {
            if (container && container.requestFullscreen) {
                container.requestFullscreen().catch(() => {
                    if (fallbackVideo && fallbackVideo.requestFullscreen) {
                        fallbackVideo.requestFullscreen();
                    }
                });
            } else if (fallbackVideo && fallbackVideo.requestFullscreen) {
                fallbackVideo.requestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    if (btnFullscreen) {
        btnFullscreen.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleContainerFullscreen(cleanPlayerContainer, cleanedVideo);
        });
    }

    if (btnPreviewFullscreen) {
        btnPreviewFullscreen.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleContainerFullscreen(previewPlayerContainer, sourceVideo);
        });
    }

    // ==========================================
    // MODE SWITCHER (SINGLE VIDEO vs BULK VIDEOS)
    // ==========================================
    const tabSingleMode = document.getElementById('tabSingleMode');
    const tabBulkMode = document.getElementById('tabBulkMode');
    const bulkUploadCard = document.getElementById('bulkUploadCard');
    const bulkDropzone = document.getElementById('bulkDropzone');
    const bulkVideoInput = document.getElementById('bulkVideoInput');
    const bulkBrowseBtn = document.getElementById('bulkBrowseBtn');
    if (bulkBrowseBtn) {
        bulkBrowseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (bulkVideoInput) bulkVideoInput.click();
        });
    }
    const bulkQueueCard = document.getElementById('bulkQueueCard');
    const bulkCounterPill = document.getElementById('bulkCounterPill');
    const btnAddMoreBulk = document.getElementById('btnAddMoreBulk');
    const btnClearBulkQueue = document.getElementById('btnClearBulkQueue');
    const bulkSummaryBar = document.getElementById('bulkSummaryBar');
    const bulkSummaryTitle = document.getElementById('bulkSummaryTitle');
    const bulkSummaryStats = document.getElementById('bulkSummaryStats');
    const bulkMasterFill = document.getElementById('bulkMasterFill');
    const bulkQueueList = document.getElementById('bulkQueueList');
    const bulkDockStatusText = document.getElementById('bulkDockStatusText');
    const btnStartBulkProcess = document.getElementById('btnStartBulkProcess');
    const bulkStartBtnText = document.getElementById('bulkStartBtnText');
    const btnDownloadBulkZip = document.getElementById('btnDownloadBulkZip');
    const bulkUploadCompleteModal = document.getElementById('bulkUploadCompleteModal');
    const btnCloseBulkReadyModal = document.getElementById('btnCloseBulkReadyModal');
    const btnModalBulkSetupCaptions = document.getElementById('btnModalBulkSetupCaptions');
    const btnModalBulkQuickClean = document.getElementById('btnModalBulkQuickClean');
    const btnModalBulkEditStart = btnModalBulkSetupCaptions;
    const btnModalReviewQueue = btnModalBulkQuickClean;
    const bulkReadyModalCount = document.getElementById('bulkReadyModalCount');

    // 2-Step Bulk Watermark-Only Modals: Step 1 Format & Step 2 Quality
    const bulkDownloadFormatModal = document.getElementById('bulkDownloadFormatModal');
    const btnCloseBulkFormatModal = document.getElementById('btnCloseBulkFormatModal');
    const cardFormatSingle = document.getElementById('cardFormatSingle');
    const cardFormatZip = document.getElementById('cardFormatZip');
    const btnNextToQuality = document.getElementById('btnNextToQuality');

    const bulkQualitySelectModal = document.getElementById('bulkQualitySelectModal');
    const btnCloseBulkQualityModal = document.getElementById('btnCloseBulkQualityModal');
    const btnBackToFormatModal = document.getElementById('btnBackToFormatModal');
    const btnStartBulkConfirmed = document.getElementById('btnStartBulkConfirmed');

    let bulkDownloadFormat = 'single'; // 'single' (MP4 one-by-one) or 'zip' (single ZIP)
    window.bulkDownloadFormat = bulkDownloadFormat;
    let bulkChosenQuality = '1080';    // 'original', '720', '1080', '4k'

    let currentMode = 'single';
    let bulkQueue = [];
    window.bulkQueue = bulkQueue;
    let isBulkProcessing = false;
    Object.defineProperty(window, 'isBulkProcessing', { get: () => isBulkProcessing, set: (v) => { isBulkProcessing = v; }, configurable: true });

    function formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // formatTime already defined above (line ~1297) — using unified version

    function formatCountdown(seconds) {
        if (!seconds || isNaN(seconds) || seconds <= 0) return '00:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function switchMode(mode) {
        currentMode = mode;
        if (mode === 'single') {
            state.isBulkStudioMode = false;
            if (tabSingleMode) tabSingleMode.classList.add('active');
            if (tabBulkMode) tabBulkMode.classList.remove('active');
            if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
            if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
            if (bulkDownloadFormatModal) bulkDownloadFormatModal.classList.add('hidden');
            if (bulkQualitySelectModal) bulkQualitySelectModal.classList.add('hidden');

            if (state.currentFilename) {
                if (uploadCard) uploadCard.classList.add('hidden');
                if (previewActionCard) previewActionCard.classList.remove('hidden');
                document.body.classList.add('studio-view-active');
                if (heroSection) heroSection.classList.add('collapsed');
            } else {
                if (uploadCard) uploadCard.classList.remove('hidden');
                if (previewActionCard) previewActionCard.classList.add('hidden');
                if (resultCard) resultCard.classList.add('hidden');
            }
        } else {
            if (tabBulkMode) tabBulkMode.classList.add('active');
            if (tabSingleMode) tabSingleMode.classList.remove('active');
            if (uploadCard) uploadCard.classList.add('hidden');
            if (!state.isBulkStudioMode) {
                if (previewActionCard) previewActionCard.classList.add('hidden');
            }
            if (resultCard) resultCard.classList.add('hidden');

            // If a single video was already uploaded, or if bulk queue has items, or if heroSection is collapsed:
            // KEEP heroSection collapsed and KEEP studio-view-active so the sleek compact style NEVER changes or jumps!
            if (state.currentFilename || (bulkQueue && bulkQueue.length > 0) || (heroSection && heroSection.classList.contains('collapsed'))) {
                document.body.classList.add('studio-view-active');
                if (heroSection) heroSection.classList.add('collapsed');
            }

            if (bulkQueue && bulkQueue.length > 0 && !state.isBulkStudioMode) {
                if (bulkQueueCard) bulkQueueCard.classList.remove('hidden');
                if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
            } else if (!state.isBulkStudioMode) {
                if (bulkUploadCard) bulkUploadCard.classList.remove('hidden');
                if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
            }
        }
    }

    if (tabSingleMode) tabSingleMode.addEventListener('click', () => switchMode('single'));
    if (tabBulkMode) tabBulkMode.addEventListener('click', () => switchMode('bulk'));

    // Fast client-side canvas thumbnail generator
    function generateVideoThumbnail(file) {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            video.preload = 'metadata';
            video.muted = true;
            video.playsInline = true;
            const objUrl = URL.createObjectURL(file);
            video.src = objUrl;

            let isResolved = false;
            const finish = () => {
                if (isResolved) return;
                isResolved = true;
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = 128;
                    canvas.height = 128;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const thumbUrl = canvas.toDataURL('image/jpeg', 0.85);
                    const duration = video.duration || 0;
                    URL.revokeObjectURL(objUrl);
                    resolve({ thumbUrl, duration });
                } catch (e) {
                    URL.revokeObjectURL(objUrl);
                    resolve({ thumbUrl: null, duration: 0 });
                }
            };

            video.onloadeddata = () => {
                video.currentTime = Math.min(0.5, (video.duration || 1) / 2);
            };
            video.onseeked = finish;
            video.onerror = () => {
                if (!isResolved) {
                    isResolved = true;
                    URL.revokeObjectURL(objUrl);
                    resolve({ thumbUrl: null, duration: 0 });
                }
            };
            setTimeout(finish, 2000);
        });
    }

    async function handleBulkFiles(files) {
        if (!files || files.length === 0) return;
        const validVideos = Array.from(files).filter(f => f.type.startsWith('video/') || f.name.match(/\.(mp4|mov|webm|avi|mkv)$/i));
        if (validVideos.length === 0) {
            alert('Please select valid video files (MP4, MOV, WEBM, AVI).');
            return;
        }

        const remainingSlots = 50 - bulkQueue.length;
        if (remainingSlots <= 0) {
            alert('Maximum 50 videos limit reached in bulk queue.');
            return;
        }

        const toAdd = validVideos.slice(0, remainingSlots);
        if (validVideos.length > remainingSlots) {
            alert(`Added ${remainingSlots} videos (Maximum 50 videos limit).`);
        }

        const newItems = toAdd.map(file => ({
            id: 'bulk_' + Math.random().toString(36).substr(2, 9),
            file: file,
            name: file.name,
            sizeStr: formatFileSize(file.size),
            durationStr: '...',
            thumbUrl: null,
            status: 'ready',
            percent: 0,
            taskId: null,
            downloadUrl: null,
            error: null
        }));

        bulkQueue = bulkQueue.concat(newItems);
        renderBulkQueue();
        switchMode('bulk');

        // Step 1 / Step 2 export choice modals ONLY appear when Watermark Remove ONLY is active!
        // When Caption Add is active, open Bulk Studio with Video 1 immediately so user can style captions without delay!
        if (bulkQueue.length > 0 && !isBulkProcessing) {
            if (captionState.isCaptionAddActive) {
                setTimeout(() => {
                    openBulkStudioWithFirstVideo();
                }, 100);
            } else {
                setTimeout(() => {
                    showBulkDownloadFormatModal();
                }, 100);
            }
        }

        // Generate thumbnails asynchronously in the background without blocking studio initialization
        (async () => {
            for (const item of newItems) {
                try {
                    const meta = await generateVideoThumbnail(item.file);
                    item.thumbUrl = meta.thumbUrl;
                    item.duration = meta.duration || 0;
                    item.durationStr = formatTime(meta.duration);
                    updateBulkItemRow(item);
                } catch (te) {
                    console.log('Thumbnail generation notice:', te);
                }
            }
        })();

        // Pre-transcribe remaining bulk videos sequentially in the background so captions are accurate & ready!
        (async () => {
            for (let i = 0; i < newItems.length; i++) {
                const it = newItems[i];
                if (!it.transcription && !it.isTranscribing && it.file) {
                    it.isTranscribing = true;
                    try {
                        const fd = new FormData();
                        fd.append('video', it.file);
                        fd.append('skip_preclean', 'true');
                        const res = await fetch('/api/upload', { method: 'POST', body: fd });
                        const data = await res.json();
                        if (data.success) {
                            it.serverFilename = data.filename;
                            it.metadata = data.metadata;
                            it.cleanVideoUrl = data.clean_video_url;
                            it.cleanFilename = data.clean_filename;
                            it.transcription = data.transcription;
                            // If user is currently looking at this item in Bulk Studio, refresh it live!
                            if (state.isBulkStudioMode && bulkQueue[state.currentBulkIndex] === it) {
                                loadBulkPreviewVideo(it);
                            }
                        }
                    } catch (err) {
                        console.log('Background queue transcription notice:', err);
                    } finally {
                        it.isTranscribing = false;
                    }
                }
            }
        })();
    }
    window.handleBulkFiles = handleBulkFiles;
    window.renderBulkQueue = renderBulkQueue;
    window.updateBulkItemRow = updateBulkItemRow;
    window.getBulkQueue = () => bulkQueue;
    window.setBulkQueue = (q) => { bulkQueue = q; renderBulkQueue(); };
    window.createBulkItemElement = createBulkItemElement;

    // ----------------------------------------------------
    // BULK EXPORT IN-PAGE CARDS: STEP 1 (FORMAT) & STEP 2 (QUALITY)
    // ----------------------------------------------------
    const pillPresetFormat = document.getElementById('pillPresetFormat');
    const pillPresetQuality = document.getElementById('pillPresetQuality');
    const presetFormatLabel = document.getElementById('presetFormatLabel');
    const presetQualityLabel = document.getElementById('presetQualityLabel');

    function updateBulkPresetLabels() {
        if (presetFormatLabel) {
            presetFormatLabel.textContent = bulkDownloadFormat === 'single' ? '⚡ Separate MP4s' : '📁 ZIP Archive';
        }
        if (presetQualityLabel) {
            const qNames = { 'original': 'Source Original', '720': '720p HD', '1080': '1080p FHD', '4k': '4K Ultra HD' };
            presetQualityLabel.textContent = '✨ ' + (qNames[bulkChosenQuality] || '1080p FHD');
        }
    }

    if (pillPresetFormat) {
        pillPresetFormat.addEventListener('click', (e) => {
            e.stopPropagation();
            showBulkDownloadFormatModal();
        });
    }

    if (pillPresetQuality) {
        pillPresetQuality.addEventListener('click', (e) => {
            e.stopPropagation();
            showBulkQualitySelectModal();
        });
    }

    function showBulkDownloadFormatModal() {
        if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
        if (bulkQualitySelectModal) bulkQualitySelectModal.classList.add('hidden');
        if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
        if (bulkDownloadFormatModal) {
            bulkDownloadFormatModal.classList.remove('hidden');
            if (cardFormatSingle && cardFormatZip) {
                if (bulkDownloadFormat === 'single') {
                    cardFormatSingle.classList.add('active');
                    cardFormatZip.classList.remove('active');
                } else {
                    cardFormatZip.classList.add('active');
                    cardFormatSingle.classList.remove('active');
                }
            }
        }
    }
    window.showBulkDownloadFormatModal = showBulkDownloadFormatModal;

    function closeBulkDownloadFormatModal() {
        if (bulkDownloadFormatModal) bulkDownloadFormatModal.classList.add('hidden');
        if (bulkQualitySelectModal) bulkQualitySelectModal.classList.add('hidden');
        if (bulkQueue && bulkQueue.length > 0) {
            if (bulkQueueCard) bulkQueueCard.classList.remove('hidden');
        } else {
            if (bulkUploadCard) bulkUploadCard.classList.remove('hidden');
        }
    }

    function showBulkQualitySelectModal() {
        if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
        if (bulkDownloadFormatModal) bulkDownloadFormatModal.classList.add('hidden');
        if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
        if (bulkQualitySelectModal) {
            bulkQualitySelectModal.classList.remove('hidden');
            const targetQ = bulkChosenQuality || state.selectedQuality || '1080';
            const cards = document.querySelectorAll('#bulkQualitySelectModal .bulk-quality-card');
            cards.forEach(card => {
                if (card.getAttribute('data-quality') === targetQ) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            });
        }
    }
    window.showBulkQualitySelectModal = showBulkQualitySelectModal;

    function closeBulkQualitySelectModal() {
        if (bulkQualitySelectModal) bulkQualitySelectModal.classList.add('hidden');
        if (bulkDownloadFormatModal) bulkDownloadFormatModal.classList.add('hidden');
        if (bulkQueue && bulkQueue.length > 0) {
            if (bulkQueueCard) bulkQueueCard.classList.remove('hidden');
        } else {
            if (bulkUploadCard) bulkUploadCard.classList.remove('hidden');
        }
    }

    function setBulkDownloadFormat(format) {
        bulkDownloadFormat = format;
        window.bulkDownloadFormat = format;
        if (cardFormatSingle && cardFormatZip) {
            if (format === 'single') {
                cardFormatSingle.classList.add('active');
                cardFormatZip.classList.remove('active');
            } else {
                cardFormatZip.classList.add('active');
                cardFormatSingle.classList.remove('active');
            }
        }
        if (chipStudioSingle && chipStudioZip) {
            if (format === 'single') {
                chipStudioSingle.classList.add('active');
                chipStudioZip.classList.remove('active');
            } else {
                chipStudioZip.classList.add('active');
                chipStudioSingle.classList.remove('active');
            }
        }
        if (studioBulkFormatBadge) {
            studioBulkFormatBadge.textContent = format === 'single' ? 'Separate MP4s' : 'ZIP Archive';
        }
        updateBulkPresetLabels();
    }
    window.setBulkDownloadFormat = setBulkDownloadFormat;

    if (cardFormatSingle) cardFormatSingle.addEventListener('click', () => setBulkDownloadFormat('single'));
    if (cardFormatZip) cardFormatZip.addEventListener('click', () => setBulkDownloadFormat('zip'));
    if (chipStudioSingle) chipStudioSingle.addEventListener('click', () => setBulkDownloadFormat('single'));
    if (chipStudioZip) chipStudioZip.addEventListener('click', () => setBulkDownloadFormat('zip'));

    if (btnNextToQuality) {
        btnNextToQuality.addEventListener('click', () => {
            closeBulkDownloadFormatModal();
            showBulkQualitySelectModal();
        });
    }

    if (btnCloseBulkFormatModal) {
        btnCloseBulkFormatModal.addEventListener('click', closeBulkDownloadFormatModal);
    }

    const modalQualityCards = document.querySelectorAll('#bulkQualitySelectModal .bulk-quality-card');
    modalQualityCards.forEach(card => {
        card.addEventListener('click', () => {
            modalQualityCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            bulkChosenQuality = card.getAttribute('data-quality') || '1080';
            updateBulkPresetLabels();
        });
    });

    if (btnBackToFormatModal) {
        btnBackToFormatModal.addEventListener('click', () => {
            closeBulkQualitySelectModal();
            showBulkDownloadFormatModal();
        });
    }

    if (btnCloseBulkQualityModal) {
        btnCloseBulkQualityModal.addEventListener('click', closeBulkQualitySelectModal);
    }

    if (btnStartBulkConfirmed) {
        btnStartBulkConfirmed.addEventListener('click', () => {
            closeBulkQualitySelectModal();
            if (bulkDownloadFormatModal) bulkDownloadFormatModal.classList.add('hidden');
            state.selectedQuality = bulkChosenQuality;
            startBulkProcessing(bulkDownloadFormat, bulkChosenQuality);
        });
    }

    function renderBulkQueue() {
        if (!bulkQueueList) return;
        bulkQueueList.innerHTML = '';
        if (bulkCounterPill) bulkCounterPill.textContent = `${bulkQueue.length} / 50 Videos`;

        if (bulkQueue.length === 0) {
            if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
            if (bulkUploadCard) bulkUploadCard.classList.remove('hidden');
            if (heroSection) heroSection.classList.remove('collapsed');
            return;
        }

        if (bulkQueueCard) bulkQueueCard.classList.remove('hidden');
        if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
        if (heroSection) heroSection.classList.add('collapsed');

        bulkQueue.forEach((item, idx) => {
            const row = createBulkItemElement(item, idx);
            bulkQueueList.appendChild(row);
        });

        updateBulkCounters();
    }

    function getSpeechBadgeHtml(item) {
        if (!captionState.isCaptionAddActive) return '';
        if (item.hasUserEditedSubtitles && item.customCues && item.customCues.length > 0) {
            return `<span class="bulk-speech-pill pill-voice" title="Custom subtitles applied">✏️ Subtitles (${item.customCues.length})</span>`;
        }
        if (item.transcription) {
            if (item.transcription.has_speech && item.transcription.cues && item.transcription.cues.length > 0) {
                return `<span class="bulk-speech-pill pill-voice" title="Voice detected: Burning subtitles">🎤 Voice (${item.transcription.cues.length} Cues)</span>`;
            } else {
                return `<span class="bulk-speech-pill pill-no-voice" title="No speech detected: Watermark removed cleanly without text">🔇 No Voice (Clean Only)</span>`;
            }
        }
        return '';
    }

    function createBulkItemElement(item, idx) {
        const div = document.createElement('div');
        div.className = `bulk-queue-item ${item.status === 'processing' ? 'is-processing' : ''} ${item.status === 'completed' ? 'is-completed' : ''}`;
        div.id = `item_${item.id}`;

        const thumbHtml = item.thumbUrl
            ? `<img class="bulk-item-thumb-img" src="${item.thumbUrl}" alt="Thumb">`
            : `<div style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:#00f2fe;">🎬</div>`;

        let rightActionsHtml = '';
        if (item.status === 'ready') {
            const hasCustom = item.customCues && item.customCues.length > 0;
            const viewEditBtnHtml = captionState.isCaptionAddActive ? `
                <button type="button" class="btn-bulk-view" onclick="openBulkStudioForIndex(${idx})" title="View video & customize subtitles">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    <span>${hasCustom ? '✏️ Subtitles' : '👁️ View / Edit'}</span>
                </button>
            ` : '';
            rightActionsHtml = `
                ${viewEditBtnHtml}
                <span class="bulk-status-badge status-ready">Ready</span>
                <button type="button" class="btn-remove-item" onclick="removeBulkItem('${item.id}')" title="Remove">✕</button>
            `;
        } else if (item.status === 'processing' || item.status === 'uploading') {
            rightActionsHtml = `
                <span class="bulk-status-badge status-processing">⚡ ${item.percent}%</span>
            `;
        } else if (item.status === 'completed') {
            rightActionsHtml = `
                <span class="status-check-done-icon" title="Watermark Removed Successfully">✓</span>
                <span class="bulk-status-badge status-done">Cleaned</span>
            `;
        } else if (item.status === 'stopped') {
            rightActionsHtml = `
                <span class="bulk-status-badge" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3)">⏹ Stopped</span>
            `;
        } else if (item.status === 'error') {
            rightActionsHtml = `
                <span class="bulk-status-badge" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3)">Failed</span>
            `;
        }

        const speechBadgeHtml = getSpeechBadgeHtml(item);

        div.innerHTML = `
            <span class="bulk-item-index">#${idx + 1}</span>
            <div class="bulk-item-thumb-wrapper">
                ${thumbHtml}
                <span class="bulk-item-duration-tag">${item.durationStr}</span>
            </div>
            <div class="bulk-item-details">
                <div class="bulk-item-topline">
                    <div style="display:flex;align-items:center;min-width:0;overflow:hidden;flex-wrap:wrap;gap:4px;">
                        <span class="bulk-item-filename" title="${item.name}">${item.name}</span>
                        <span class="speech-badge-slot">${speechBadgeHtml}</span>
                    </div>
                </div>
                <div class="bulk-item-progress-line">
                    <div class="bulk-item-progress-fill" style="width: ${item.percent}%"></div>
                </div>
            </div>
            <div class="bulk-item-right" id="right_${item.id}">
                ${rightActionsHtml}
            </div>
        `;
        return div;
    }

    function updateBulkItemRow(item) {
        const row = document.getElementById(`item_${item.id}`);
        if (!row) return;

        row.className = `bulk-queue-item ${item.status === 'processing' ? 'is-processing' : ''} ${item.status === 'completed' ? 'is-completed' : ''}`;

        const thumbWrap = row.querySelector('.bulk-item-thumb-wrapper');
        if (thumbWrap && item.thumbUrl && !thumbWrap.querySelector('img')) {
            thumbWrap.innerHTML = `
                <img class="bulk-item-thumb-img" src="${item.thumbUrl}" alt="Thumb">
                <span class="bulk-item-duration-tag">${item.durationStr}</span>
            `;
        }

        const fill = row.querySelector('.bulk-item-progress-fill');
        if (fill) fill.style.width = `${item.percent}%`;

        const speechSlot = row.querySelector('.speech-badge-slot');
        if (speechSlot) speechSlot.innerHTML = getSpeechBadgeHtml(item);

        const rightArea = document.getElementById(`right_${item.id}`);
        if (!rightArea) return;

        if (item.status === 'ready') {
            const idx = bulkQueue.findIndex(i => i.id === item.id);
            const targetIdx = idx >= 0 ? idx : 0;
            const hasCustom = item.customCues && item.customCues.length > 0;
            const viewEditBtnHtml = captionState.isCaptionAddActive ? `
                <button type="button" class="btn-bulk-view" onclick="openBulkStudioForIndex(${targetIdx})" title="View video & customize subtitles">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    <span>${hasCustom ? '✏️ Subtitles' : '👁️ View / Edit'}</span>
                </button>
            ` : '';
            rightArea.innerHTML = `
                ${viewEditBtnHtml}
                <span class="bulk-status-badge status-ready">Ready</span>
                <button type="button" class="btn-remove-item" onclick="removeBulkItem('${item.id}')" title="Remove">✕</button>
            `;
        } else if (item.status === 'processing' || item.status === 'uploading') {
            rightArea.innerHTML = `
                <span class="bulk-status-badge status-processing">⚡ ${item.percent}%</span>
            `;
        } else if (item.status === 'completed') {
            rightArea.innerHTML = `
                <span class="status-check-done-icon" title="Watermark Removed Successfully">✓</span>
                <span class="bulk-status-badge status-done">Cleaned</span>
            `;
        } else if (item.status === 'stopped') {
            rightArea.innerHTML = `
                <span class="bulk-status-badge" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3)">⏹ Stopped</span>
            `;
        } else if (item.status === 'error') {
            rightArea.innerHTML = `
                <span class="bulk-status-badge" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3)">Failed</span>
            `;
        }
    }

    window.removeBulkItem = function(id) {
        if (isBulkProcessing) return;
        bulkQueue = bulkQueue.filter(i => i.id !== id);
        renderBulkQueue();
    };

    if (btnClearBulkQueue) {
        btnClearBulkQueue.addEventListener('click', () => {
            if (isBulkProcessing) return;
            bulkQueue = [];
            renderBulkQueue();
        });
    }

    const btnStopBulkBatch = document.getElementById('btnStopBulkBatch');
    const bulkSummaryBadge = document.getElementById('bulkSummaryBadge');
    let isBulkBatchAborted = false;

    if (btnStopBulkBatch) {
        btnStopBulkBatch.addEventListener('click', () => {
            if (!isBulkProcessing) return;
            stopAllBulkProcessing();
        });
    }

    function stopAllBulkProcessing() {
        isBulkBatchAborted = true;
        isBulkProcessing = false;
        if (btnStopBulkBatch) {
            btnStopBulkBatch.disabled = true;
            btnStopBulkBatch.classList.remove('is-active');
        }
        if (bulkSummaryTitle) {
            bulkSummaryTitle.textContent = '⏹ Bulk Processing Stopped by User';
        }
        if (bulkSummaryBadge) {
            bulkSummaryBadge.textContent = '⏹ STOPPED';
            bulkSummaryBadge.style.background = 'rgba(239, 68, 68, 0.2)';
            bulkSummaryBadge.style.color = '#ef4444';
            bulkSummaryBadge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        }
        if (bulkDockStatusText) {
            bulkDockStatusText.textContent = 'Bulk processing stopped by user.';
        }
        if (btnStartBulkProcess) btnStartBulkProcess.disabled = false;
        if (btnClearBulkQueue) btnClearBulkQueue.disabled = false;
        if (btnAddMoreBulk) btnAddMoreBulk.disabled = false;
        if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = false;

        bulkQueue.forEach(item => {
            if (item.status === 'processing' || item.status === 'ready') {
                item.status = 'stopped';
                item.etaStr = '';
                updateBulkItemRow(item);
            }
        });
        updateBulkCounters();
    }

    function updateBulkCounters() {
        const completed = bulkQueue.filter(i => i.status === 'completed').length;
        const total = bulkQueue.length;
        if (bulkCounterPill) bulkCounterPill.textContent = `${total} / 50 Videos`;
        if (bulkSummaryStats) bulkSummaryStats.textContent = `Completed ${completed} of ${total}`;
        const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
        if (bulkMasterFill) bulkMasterFill.style.width = `${pct}%`;

        // Keep only ONE primary download button to prevent duplicate buttons in Image 2
        if (btnDownloadBulkZip) {
            btnDownloadBulkZip.classList.add('hidden');
        }

        if (!isBulkProcessing) {
            if (completed === total && total > 0) {
                // All videos are completed: primary action is Download All (or single video)
                if (bulkStartBtnText) {
                    bulkStartBtnText.textContent = total > 1 ? `⬇ Download All Videos (ZIP)` : `⬇ Download Video`;
                }
                if (btnStartBulkProcess) {
                    btnStartBulkProcess.classList.remove('hidden');
                    btnStartBulkProcess.style.display = 'inline-flex';
                }
            } else {
                // Processing not completed yet.
                // Image 4 requirement: If only watermark removal is selected, show "Remove Watermark" instead of "Download All"
                const isOnlyWatermark = !captionState.isCaptionAddActive;
                if (bulkStartBtnText) {
                    if (isOnlyWatermark) {
                        bulkStartBtnText.textContent = total > 1 ? `⚡ Remove Watermarks (${total} Videos)` : `⚡ Remove Watermark`;
                    } else {
                        bulkStartBtnText.textContent = total > 1 ? `⬇ Download All (${total} Videos)` : `⬇ Download`;
                    }
                }
                if (btnStartBulkProcess) {
                    btnStartBulkProcess.classList.remove('hidden');
                    btnStartBulkProcess.style.display = 'inline-flex';
                }
            }
        }
    }

    if (bulkVideoInput) {
        bulkVideoInput.addEventListener('change', (e) => {
            handleBulkFiles(e.target.files);
            bulkVideoInput.value = '';
        });
    }

    if (bulkDropzone) {
        ['dragenter', 'dragover'].forEach(name => {
            bulkDropzone.addEventListener(name, (e) => {
                e.preventDefault();
                bulkDropzone.classList.add('dragover');
            });
        });
        ['dragleave', 'drop'].forEach(name => {
            bulkDropzone.addEventListener(name, (e) => {
                e.preventDefault();
                bulkDropzone.classList.remove('dragover');
            });
        });
        bulkDropzone.addEventListener('drop', (e) => {
            if (e.dataTransfer && e.dataTransfer.files) {
                handleBulkFiles(e.dataTransfer.files);
            }
        });
    }

    function triggerSingleVideoDownload(item, quality) {
        if (!item || !item.taskId) return;
        const q = quality || state.selectedQuality || '1080';
        const a = document.createElement('a');
        a.href = `/api/download/${item.taskId}?quality=${q}`;
        const cleanBase = (item.name || 'video').replace(/\.[^/.]+$/, "");
        a.download = `dolaedits_${q}_${cleanBase}.mp4`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => a.remove(), 1200);
    }

    async function startBulkProcessing(formatMode, chosenQuality) {
        if (isBulkProcessing || bulkQueue.length === 0) return;

        const format = formatMode || bulkDownloadFormat || 'single';
        const q = chosenQuality || bulkChosenQuality || state.selectedQuality || '1080';
        state.selectedQuality = q;
        const qName = (q === '4k') ? '4K Ultra HD' : ((q === '720') ? '720p HD' : ((q === 'original') ? 'Original' : '1080p FHD'));

        const pendingItems = bulkQueue.filter(i => i.status === 'ready' || i.status === 'error' || i.status === 'stopped');
        if (pendingItems.length === 0) {
            const completedItems = bulkQueue.filter(i => i.status === 'completed' && i.taskId);
            if (completedItems.length === 1 && completedItems[0].downloadUrl) {
                const a = document.createElement('a');
                a.href = completedItems[0].downloadUrl;
                a.download = '';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else if (completedItems.length > 1 && btnDownloadBulkZip) {
                btnDownloadBulkZip.click();
            } else {
                alert('All videos in queue have already been processed!');
            }
            return;
        }

        isBulkProcessing = true;
        isBulkBatchAborted = false;
        if (btnStopBulkBatch) {
            btnStopBulkBatch.disabled = false;
            btnStopBulkBatch.classList.add('is-active');
        }
        if (btnStartBulkProcess) btnStartBulkProcess.disabled = true;
        if (btnClearBulkQueue) btnClearBulkQueue.disabled = true;
        if (btnAddMoreBulk) btnAddMoreBulk.disabled = true;
        if (bulkStartBtnText) bulkStartBtnText.textContent = 'Processing Videos...';
        if (bulkSummaryBar) bulkSummaryBar.classList.remove('hidden');
        if (bulkSummaryBadge) {
            bulkSummaryBadge.textContent = '⚡ ACTIVE BATCH ENGINE';
            bulkSummaryBadge.style.background = '';
            bulkSummaryBadge.style.color = '';
            bulkSummaryBadge.style.borderColor = '';
        }
        if (bulkDockStatusText) bulkDockStatusText.textContent = `⚡ Processing videos [${qName}]...`;

        const totalItems = pendingItems.length;

        for (let idx = 0; idx < pendingItems.length; idx++) {
            if (isBulkBatchAborted) break;
            const item = pendingItems[idx];
            if (bulkSummaryTitle) {
                bulkSummaryTitle.textContent = `Processing Video ${idx + 1} of ${totalItems}: ${item.name} [${qName}]...`;
            }
            if (bulkSummaryStats) {
                bulkSummaryStats.textContent = `Completed ${idx} of ${totalItems}`;
            }
            if (bulkMasterFill) {
                bulkMasterFill.style.width = `${Math.round((idx / totalItems) * 100)}%`;
            }

            await processSingleBulkItem(item, idx, totalItems, q);
            if (isBulkBatchAborted) break;

            // As requested in Img 2: advance progress line forward cleanly as each video completes
            if (bulkMasterFill) {
                bulkMasterFill.style.width = `${Math.round(((idx + 1) / totalItems) * 100)}%`;
            }
            if (bulkSummaryStats) {
                bulkSummaryStats.textContent = `Completed ${idx + 1} of ${totalItems}`;
            }

            // User requirement: If single video download selected, download MP4 immediately on completion of each video!
            if (format === 'single' && item.status === 'completed' && item.taskId) {
                triggerSingleVideoDownload(item, q);
            }

            updateBulkCounters();
        }

        isBulkProcessing = false;
        if (btnStopBulkBatch) {
            btnStopBulkBatch.disabled = true;
            btnStopBulkBatch.classList.remove('is-active');
        }
        if (btnStartBulkProcess) btnStartBulkProcess.disabled = false;
        if (btnClearBulkQueue) btnClearBulkQueue.disabled = false;
        if (btnAddMoreBulk) btnAddMoreBulk.disabled = false;
        if (bulkDockStatusText) bulkDockStatusText.textContent = '🎉 All bulk videos processed!';
        updateBulkCounters();

        if (!isBulkBatchAborted) {
            const completedItems = bulkQueue.filter(i => i.status === 'completed' && i.taskId);
            if (completedItems.length > 0) {
                const taskIds = completedItems.map(i => i.taskId);
                if (bulkSummaryTitle) bulkSummaryTitle.textContent = `🎉 All ${completedItems.length} Videos Completed! [${qName}]`;
                if (bulkSummaryStats) bulkSummaryStats.textContent = `Completed ${completedItems.length} of ${completedItems.length} (100%)`;
                if (bulkMasterFill) bulkMasterFill.style.width = '100%';

                // User requirement: "zip file dawnload ho jaye fir popup dena hai"
                if (format === 'zip') {
                    if (bulkSummaryTitle) bulkSummaryTitle.textContent = `📦 Downloading ZIP Archive (${completedItems.length} Videos)...`;
                    if (bulkDockStatusText) bulkDockStatusText.textContent = '📦 Downloading your ZIP archive to device...';
                    await triggerBatchZipDownload(taskIds, q);
                    showBulkAllDoneModal(completedItems.length, qName, taskIds, q, format);
                } else {
                    showBulkAllDoneModal(completedItems.length, qName, taskIds, q, format);
                }
            }
        }
    }

    async function processSingleBulkItem(item, itemIdx = 0, totalItems = 1, chosenQuality = '1080') {
        if (isBulkBatchAborted) return;
        item.status = 'processing';
        item.percent = 8;
        updateBulkItemRow(item);

        try {
            let serverFilename = item.serverFilename;
            let videoCues = null;

            if (!serverFilename) {
                const formData = new FormData();
                formData.append('video', item.file);
                // Transcribe only if Caption Add is selected
                if (!captionState.isCaptionAddActive) {
                    formData.append('skip_transcription', 'true');
                }
                formData.append('skip_preclean', 'true');
                const uploadRes = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                if (!uploadRes.ok) throw new Error('Upload failed');
                const uploadData = await uploadRes.json();
                if (!uploadData.success) throw new Error(uploadData.error || 'Upload failed');
                serverFilename = uploadData.filename;
                item.serverFilename = serverFilename;
                if (uploadData.transcription) {
                    item.transcription = uploadData.transcription;
                }
            } else if (captionState.isCaptionAddActive && !item.transcription && !item.hasUserEditedSubtitles) {
                try {
                    const trRes = await fetch('/api/transcribe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filename: serverFilename })
                    });
                    if (trRes.ok) {
                        const trData = await trRes.json();
                        if (trData.success) item.transcription = trData;
                    }
                } catch (te) {
                    console.warn('Transcription fetch warning:', te);
                }
            }

            if (isBulkBatchAborted) {
                item.status = 'stopped';
                updateBulkItemRow(item);
                return;
            }

            item.percent = 18;
            updateBulkItemRow(item);

            // Determine video subtitle cues:
            // CRITICAL:
            // 1. User custom cues for this video > 2. This video's OWN speech transcription > 3. EMPTY
            // NEVER fall back to dummy English cues! If no speech, NO subtitles added!
            if (item.hasUserEditedSubtitles && item.customCues && item.customCues.length > 0) {
                videoCues = item.customCues;
            } else if (captionState.isCaptionAddActive && item.transcription && item.transcription.has_speech && item.transcription.cues && item.transcription.cues.length > 0) {
                videoCues = item.transcription.cues;
            } else {
                videoCues = [];
            }

            const shouldAddCaptions = captionState.isCaptionAddActive && (videoCues && videoCues.length > 0);

            const procRes = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: serverFilename,
                    original_name: item.name || (item.file ? item.file.name : serverFilename),
                    remove_watermark: captionState.isWatermarkRemoveActive,
                    add_captions: shouldAddCaptions,
                    captions: videoCues,
                    caption_style: captionState.style || 'classic',
                    caption_size: captionState.fontScale || 0.052,
                    caption_line_height: captionState.lineHeight || 1.16,
                    caption_pos_y: captionState.posY || 0.85,
                    quality: chosenQuality || state.selectedQuality || '1080'
                })
            });
            if (!procRes.ok) throw new Error('Failed to start processing');
            const procData = await procRes.json();
            if (!procData.success) throw new Error(procData.error || 'Failed to start');

            item.taskId = procData.task_id;

            await new Promise((resolve, reject) => {
                const pollTimer = setInterval(async () => {
                    try {
                        if (isBulkBatchAborted) {
                            clearInterval(pollTimer);
                            item.status = 'stopped';
                            updateBulkItemRow(item);
                            resolve();
                            return;
                        }

                        const statusRes = await fetch(`/api/status/${item.taskId}`);
                        if (!statusRes.ok) throw new Error('Status check failed');
                        const statusData = await statusRes.json();

                        if (statusData.status === 'completed') {
                            clearInterval(pollTimer);
                            item.status = 'completed';
                            item.percent = 100;
                            item.downloadUrl = `/api/download/${item.taskId}?quality=${chosenQuality || state.selectedQuality || '1080'}`;
                            updateBulkItemRow(item);
                            if (bulkMasterFill) {
                                const doneOverall = Math.round(((itemIdx + 1) / totalItems) * 100);
                                bulkMasterFill.style.width = `${doneOverall}%`;
                            }
                            resolve();
                        } else if (statusData.status === 'error') {
                            clearInterval(pollTimer);
                            throw new Error(statusData.error || 'Watermark removal failed');
                        } else {
                            const rawPct = statusData.percent || 0;
                            item.percent = Math.max(18, Math.min(98, Math.round(18 + (rawPct * 0.8))));

                            // Advances global master progress line proportionally without resetting to 0!
                            const currentOverall = Math.min(99, Math.round(((itemIdx + (rawPct / 100)) / totalItems) * 100));
                            if (bulkMasterFill) bulkMasterFill.style.width = `${currentOverall}%`;

                            updateBulkItemRow(item);
                        }
                    } catch (err) {
                        clearInterval(pollTimer);
                        reject(err);
                    }
                }, 400);
            });

        } catch (err) {
            console.error('Bulk item failed:', item.name, err);
            item.status = 'error';
            item.percent = 0;
            item.error = err.message;
            updateBulkItemRow(item);
        }
    }

    if (btnStartBulkProcess) {
        btnStartBulkProcess.addEventListener('click', () => {
            if (isBulkProcessing) return;
            const pendingItems = bulkQueue.filter(i => i.status === 'ready' || i.status === 'error' || i.status === 'stopped');
            if (pendingItems.length > 0 && captionState.isWatermarkRemoveActive && !captionState.isCaptionAddActive) {
                showBulkDownloadFormatModal();
            } else if (pendingItems.length > 0 && captionState.isCaptionAddActive) {
                openBulkStudioWithFirstVideo();
            } else {
                startBulkProcessing();
            }
        });
    }

    if (btnDownloadBulkZip) {
        btnDownloadBulkZip.addEventListener('click', () => {
            const completedTaskIds = bulkQueue.filter(i => i.status === 'completed' && i.taskId).map(i => i.taskId);
            if (completedTaskIds.length === 0) {
                alert('No completed videos to download.');
                return;
            }

            const originalBtnHtml = btnDownloadBulkZip.innerHTML;
            btnDownloadBulkZip.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" style="animation: spin 1s linear infinite;">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="12"></circle>
                </svg>
                <span>Preparing ZIP...</span>
            `;

            // Native browser download: zero RAM buffer, streams directly to Downloads folder!
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/api/bulk-download';
            form.style.display = 'none';

            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'task_ids';
            input.value = completedTaskIds.join(',');
            form.appendChild(input);

            document.body.appendChild(form);
            form.submit();

            setTimeout(() => {
                form.remove();
                btnDownloadBulkZip.innerHTML = originalBtnHtml;
            }, 3500);
        });
    }

    // --- BULK STUDIO INTEGRATION (SAME DESIGN AS SINGLE VIDEO) ---
    async function openBulkStudioWithIndex(targetIdx = 0) {
        if (bulkQueue.length === 0) return;
        if (targetIdx < 0 || targetIdx >= bulkQueue.length) targetIdx = 0;
        state.isBulkStudioMode = true;
        state.currentBulkIndex = targetIdx;
        currentMode = 'bulk';
        if (tabBulkMode) tabBulkMode.classList.add('active');
        if (tabSingleMode) tabSingleMode.classList.remove('active');

        // Switch to Studio layout
        document.body.classList.add('studio-view-active');
        if (heroSection) heroSection.classList.add('collapsed');
        if (uploadCard) uploadCard.classList.add('hidden');
        if (bulkUploadCard) bulkUploadCard.classList.add('hidden');
        if (bulkQueueCard) bulkQueueCard.classList.add('hidden');
        if (previewActionCard) previewActionCard.classList.remove('hidden');

        // Reveal Bulk Batch Pill & Switcher in Studio Header, hide single video header
        if (btnBackText) btnBackText.textContent = 'Back to Bulk Queue';
        if (videoInfoInline) videoInfoInline.classList.add('hidden');
        if (bulkStudioBatchPill) bulkStudioBatchPill.classList.remove('hidden');
        if (bulkStudioVideoCount) bulkStudioVideoCount.textContent = `${bulkQueue.length} Videos`;

        // Populate dropdown with all uploaded bulk videos
        if (bulkVideoPreviewSelect) {
            bulkVideoPreviewSelect.innerHTML = '';
            bulkQueue.forEach((item, idx) => {
                const opt = document.createElement('option');
                opt.value = idx;
                opt.textContent = `Video ${idx + 1}: ${item.file ? item.file.name : item.name}`;
                bulkVideoPreviewSelect.appendChild(opt);
            });
            bulkVideoPreviewSelect.value = targetIdx;

            bulkVideoPreviewSelect.onchange = (e) => {
                const selectedIdx = parseInt(e.target.value, 10);
                const prevItem = bulkQueue[state.currentBulkIndex];
                if (prevItem && prevItem.hasUserEditedSubtitles) {
                    prevItem.customFormattedText = captionTextInput ? captionTextInput.value : '';
                    prevItem.customCues = parseSubtitlesText(prevItem.customFormattedText, (state.videoMeta && state.videoMeta.duration) || 10);
                }
                state.currentBulkIndex = selectedIdx;
                const selItem = bulkQueue[selectedIdx];
                if (selItem) {
                    loadBulkPreviewVideo(selItem);
                }
            };
        }

        // Enable Caption Add mode by default
        captionState.isCaptionAddActive = true;
        captionState.isWatermarkRemoveActive = true;
        updateFeatureTogglesUI();

        // Update action button text for bulk studio mode
        if (btnCaptionEditText) {
            btnCaptionEditText.textContent = `Apply to All (${bulkQueue.length} Videos)`;
        }

        // Reveal Studio Bulk Download Format Selector and sync active format
        if (studioBulkFormatBar) {
            studioBulkFormatBar.classList.remove('hidden');
            if (chipStudioSingle && chipStudioZip) {
                if (bulkDownloadFormat === 'single') {
                    chipStudioSingle.classList.add('active');
                    chipStudioZip.classList.remove('active');
                    if (studioBulkFormatBadge) studioBulkFormatBadge.textContent = 'Separate MP4s';
                } else {
                    chipStudioZip.classList.add('active');
                    chipStudioSingle.classList.remove('active');
                    if (studioBulkFormatBadge) studioBulkFormatBadge.textContent = 'ZIP Archive';
                }
            }
        }

        // Load and setup target video
        await loadBulkPreviewVideo(bulkQueue[targetIdx]);
    }

    async function openBulkStudioWithFirstVideo() {
        await openBulkStudioWithIndex(0);
    }

    window.openBulkStudioForIndex = function(idx) {
        openBulkStudioWithIndex(idx);
    };
    window.openBulkStudioWithIndex = openBulkStudioWithIndex;

    async function loadBulkPreviewVideo(item) {
        if (!item || (!item.file && !item.cleanVideoUrl)) return;
        
        // Priority: When watermark removal is active, always use cleanVideoUrl so video player displays clean video!
        const activeSrc = (captionState.isWatermarkRemoveActive && item.cleanVideoUrl)
            ? item.cleanVideoUrl
            : (item.cleanVideoUrl || (item.file ? URL.createObjectURL(item.file) : ''));
        state.rawVideoUrl = activeSrc;
        if (captionState.isWatermarkRemoveActive && item.cleanVideoUrl) {
            state.cleanVideoUrl = item.cleanVideoUrl;
        }

        // Immediate aspect-ratio lock to prevent any 1280px tall overflow
        applyAspectRatio(previewPlayerContainer, item.metadata || { width: 720, height: 1280 });

        if (sourceVideo) {
            sourceVideo.muted = false;
            sourceVideo.volume = 1.0;
            if (previewVolIcon) previewVolIcon.classList.remove('hidden');
            if (previewMuteIcon) previewMuteIcon.classList.add('hidden');
            sourceVideo.src = activeSrc;
            sourceVideo.onloadedmetadata = () => {
                if (sourceVideo.videoWidth && sourceVideo.videoHeight) {
                    applyAspectRatio(previewPlayerContainer, { width: sourceVideo.videoWidth, height: sourceVideo.videoHeight });
                    if (bulkMetaRes) bulkMetaRes.textContent = `${sourceVideo.videoWidth}x${sourceVideo.videoHeight}`;
                    if (bulkMetaDuration) bulkMetaDuration.textContent = formatTime(sourceVideo.duration);
                }
            };
            sourceVideo.load();
        }
        if (videoFileName) videoFileName.textContent = item.name || (item.file ? item.file.name : 'Bulk Video');

        // 1. If this item already has user-edited custom subtitles, load them immediately
        if (item.hasUserEditedSubtitles && item.customCues && item.customCues.length > 0) {
            captionState.cues = item.customCues;
            renderCuesList();
            if (captionTextInput) {
                captionTextInput.value = item.customFormattedText || item.customCues.map(c => `[${formatCueTime(c.start)} - ${formatCueTime(c.end)}] ${c.text}`).join('\n');
                captionTextInput.placeholder = 'Type custom subtitles here...';
            }
            if (captionSpeechBadge) {
                captionSpeechBadge.textContent = `✏️ Custom Subtitles (${item.customCues.length} lines)`;
                captionSpeechBadge.classList.remove('hidden');
            }
            if (previewCaptionOverlay) previewCaptionOverlay.classList.remove('hidden');
            updateLiveSubtitleOverlay(sourceVideo ? (sourceVideo.currentTime || 0) : 0);
            return;
        }

        // 2. If this item already has cached transcription (with speech or without speech)
        if (item.transcription) {
            if (item.transcription.has_speech && item.transcription.cues && item.transcription.cues.length > 0) {
                captionState.cues = item.transcription.cues;
                renderCuesList();
                if (captionTextInput) {
                    captionTextInput.value = item.transcription.formatted_text || item.transcription.cues.map(c => `[${formatCueTime(c.start)} - ${formatCueTime(c.end)}] ${c.text}`).join('\n');
                    captionTextInput.placeholder = 'Type custom subtitles here...';
                }
                if (captionSpeechBadge) {
                    captionSpeechBadge.textContent = `🎙️ AI Speech Synced (${item.transcription.cues.length} lines)`;
                    captionSpeechBadge.classList.remove('hidden');
                }
                if (previewCaptionOverlay) previewCaptionOverlay.classList.remove('hidden');
                updateLiveSubtitleOverlay(sourceVideo ? (sourceVideo.currentTime || 0) : 0);
            } else {
                // Video is silent / no speech detected -> NEVER inject dummy captions!
                captionState.cues = [];
                renderCuesList();
                if (captionTextInput) {
                    captionTextInput.value = '';
                    captionTextInput.placeholder = 'No speech detected in this video. You can type custom subtitles here...';
                }
                if (captionSpeechBadge) {
                    captionSpeechBadge.textContent = '🔇 No Speech Detected (Video has no voice)';
                    captionSpeechBadge.classList.remove('hidden');
                }
                if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');
                updateLiveSubtitleOverlay(0);
            }
            return;
        }

        // 3. Not yet transcribed: Show REAL buffering indicator while Whisper processes!
        captionState.cues = [];
        renderCuesList();
        if (captionTextInput) {
            captionTextInput.value = '';
            captionTextInput.placeholder = '⏳ AI analyzing voice & syncing accurate captions... Please wait a moment...';
        }
        if (captionSpeechBadge) {
            captionSpeechBadge.textContent = '⏳ AI Transcribing Audio... Please wait...';
            captionSpeechBadge.classList.remove('hidden');
        }
        if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');

        try {
            item.isTranscribing = true;
            const formData = new FormData();
            formData.append('video', item.file);
            formData.append('skip_preclean', 'true');
            const upRes = await fetch('/api/upload', { method: 'POST', body: formData });
            const upData = await upRes.json();
            if (upData.success) {
                item.serverFilename = upData.filename;
                item.cleanVideoUrl = upData.clean_video_url;
                item.cleanFilename = upData.clean_filename;
                state.currentFilename = upData.filename;
                state.videoMeta = upData.metadata;
                item.metadata = upData.metadata;
                item.transcription = upData.transcription;

                if (captionState.isWatermarkRemoveActive && upData.clean_video_url) {
                    state.cleanVideoUrl = upData.clean_video_url;
                    if (sourceVideo && sourceVideo.src !== upData.clean_video_url) {
                        sourceVideo.src = upData.clean_video_url;
                        sourceVideo.load();
                    }
                }
                applyAspectRatio(previewPlayerContainer, upData.metadata);
                if (bulkMetaRes) bulkMetaRes.textContent = `${upData.metadata.width}x${upData.metadata.height}`;
                if (bulkMetaDuration) bulkMetaDuration.textContent = formatTime(upData.metadata.duration);
                if (metaRes) metaRes.textContent = `${upData.metadata.width}x${upData.metadata.height}`;
                if (metaDuration) metaDuration.textContent = formatTime(upData.metadata.duration);

                // Update Studio UI if user is currently previewing this video
                if (bulkQueue[state.currentBulkIndex] === item) {
                    if (item.transcription && item.transcription.has_speech && item.transcription.cues && item.transcription.cues.length > 0) {
                        if (!item.hasUserEditedSubtitles) {
                            captionState.cues = item.transcription.cues;
                            renderCuesList();
                            if (captionTextInput) {
                                captionTextInput.value = item.transcription.formatted_text || item.transcription.cues.map(c => `[${formatCueTime(c.start)} - ${formatCueTime(c.end)}] ${c.text}`).join('\n');
                                captionTextInput.placeholder = 'Type custom subtitles here...';
                            }
                            if (captionSpeechBadge) {
                                captionSpeechBadge.textContent = `🎙️ AI Speech Synced (${item.transcription.cues.length} lines)`;
                                captionSpeechBadge.classList.remove('hidden');
                            }
                            if (previewCaptionOverlay) previewCaptionOverlay.classList.remove('hidden');
                            updateLiveSubtitleOverlay(sourceVideo ? (sourceVideo.currentTime || 0) : 0);
                        }
                    } else {
                        // Silent video
                        captionState.cues = [];
                        renderCuesList();
                        if (captionTextInput) {
                            captionTextInput.value = '';
                            captionTextInput.placeholder = 'No speech detected in this video. You can type custom subtitles here...';
                        }
                        if (captionSpeechBadge) {
                            captionSpeechBadge.textContent = '🔇 No Speech Detected (Video has no voice)';
                            captionSpeechBadge.classList.remove('hidden');
                        }
                        if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');
                        updateLiveSubtitleOverlay(0);
                    }
                }
            } else {
                throw new Error(upData.error || 'Failed to analyze video');
            }
        } catch (err) {
            console.log('Bulk preview video setup notice:', err);
            captionState.cues = [];
            renderCuesList();
            if (captionTextInput) {
                captionTextInput.value = '';
                captionTextInput.placeholder = 'Transcription unavailable. You can type custom subtitles here...';
            }
            if (captionSpeechBadge) {
                captionSpeechBadge.textContent = '⚠️ Transcription Unavailable';
                captionSpeechBadge.classList.remove('hidden');
            }
            if (previewCaptionOverlay) previewCaptionOverlay.classList.add('hidden');
        } finally {
            item.isTranscribing = false;
            if (btnAutoTranscribeVoice) btnAutoTranscribeVoice.classList.remove('is-loading');
        }
    }

    // --- BULK ALL DONE MODAL & ZIP DOWNLOAD HANDLERS ---
    const bulkAllDoneModal = document.getElementById('bulkAllDoneModal');
    const btnCloseBulkDoneModal = document.getElementById('btnCloseBulkDoneModal');
    const btnDoneCloseModal = document.getElementById('btnDoneCloseModal');
    const btnDownloadAllCompletedZip = document.getElementById('btnDownloadAllCompletedZip');
    const btnSummaryDownloadZip = document.getElementById('btnSummaryDownloadZip');
    const bulkSummaryDownloadArea = document.getElementById('bulkSummaryDownloadArea');
    const bulkDoneCount = document.getElementById('bulkDoneCount');
    const bulkDoneQualityLabel = document.getElementById('bulkDoneQualityLabel');

    const bulkDoneTitle = document.getElementById('bulkDoneTitle');
    const bulkDoneSubtitle = document.getElementById('bulkDoneSubtitle');

    let lastCompletedTaskIds = [];
    let lastCompletedQuality = '1080';

    function showBulkAllDoneModal(count, qualityName, taskIds, qLabel, formatMode = 'zip') {
        lastCompletedTaskIds = taskIds || [];
        lastCompletedQuality = qLabel || '1080';
        if (bulkDoneCount) bulkDoneCount.textContent = `${count} Video${count > 1 ? 's' : ''}`;
        if (bulkDoneQualityLabel) bulkDoneQualityLabel.textContent = `✨ ${qualityName} Export Quality • Auto-Downloaded`;

        if (bulkDoneTitle && bulkDoneSubtitle) {
            if (formatMode === 'single') {
                bulkDoneTitle.textContent = '🎉 All Videos Downloaded Successfully!';
                bulkDoneSubtitle.innerHTML = `Watermarks removed across all <strong id="bulkDoneCount">${count} Videos</strong>. Each individual MP4 video file has downloaded automatically to your device.`;
            } else {
                bulkDoneTitle.textContent = '🎉 Zip File Successfully Downloaded!';
                bulkDoneSubtitle.innerHTML = `Watermarks removed across all <strong id="bulkDoneCount">${count} Videos</strong>. Your ZIP archive has downloaded automatically.`;
            }
        }
        if (bulkAllDoneModal) bulkAllDoneModal.classList.remove('hidden');
    }
    window.showBulkAllDoneModal = showBulkAllDoneModal;

    function closeBulkAllDoneModal() {
        if (bulkAllDoneModal) bulkAllDoneModal.classList.add('hidden');
    }

    if (btnCloseBulkDoneModal) {
        btnCloseBulkDoneModal.addEventListener('click', closeBulkAllDoneModal);
    }
    if (btnDoneCloseModal) {
        btnDoneCloseModal.addEventListener('click', closeBulkAllDoneModal);
    }
    if (bulkAllDoneModal) {
        bulkAllDoneModal.addEventListener('click', (e) => {
            if (e.target === bulkAllDoneModal) closeBulkAllDoneModal();
        });
    }

    async function triggerBatchZipDownload(taskIds, q) {
        if (!taskIds || taskIds.length === 0) return;
        const qLabel = q || state.selectedQuality || '1080';
        if (taskIds.length === 1) {
            const a = document.createElement('a');
            a.href = `/api/download/${taskIds[0]}?quality=${qLabel}`;
            a.download = `dolaedits_${qLabel}_${taskIds[0].slice(0, 6)}.mp4`;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => a.remove(), 1000);
            return;
        }

        try {
            const res = await fetch('/api/bulk-download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_ids: taskIds })
            });
            if (!res.ok) throw new Error('ZIP generation failed');
            const blob = await res.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = `dolaedits_bulk_${taskIds.length}_videos.zip`;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                a.remove();
                window.URL.revokeObjectURL(blobUrl);
            }, 6000);
        } catch (err) {
            console.error('ZIP blob fetch error, fallback to form submit:', err);
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/api/bulk-download';
            form.style.display = 'none';
            const inp = document.createElement('input');
            inp.type = 'hidden';
            inp.name = 'task_ids';
            inp.value = taskIds.join(',');
            form.appendChild(inp);
            document.body.appendChild(form);
            form.submit();
            setTimeout(() => form.remove(), 2500);
        }
    }

    if (btnDownloadAllCompletedZip) {
        btnDownloadAllCompletedZip.addEventListener('click', () => {
            triggerBatchZipDownload(lastCompletedTaskIds, lastCompletedQuality);
        });
    }
    if (btnSummaryDownloadZip) {
        btnSummaryDownloadZip.addEventListener('click', () => {
            triggerBatchZipDownload(lastCompletedTaskIds, lastCompletedQuality);
        });
    }

    async function executeBulkStudioBatchProcessing() {
        if (bulkQueue.length === 0) return;

        const duration = (state.videoMeta && state.videoMeta.duration) || 10;
        const currentItem = bulkQueue[state.currentBulkIndex];
        const userTypedText = captionTextInput ? captionTextInput.value.trim() : '';

        // Only set custom cues for the currently selected bulk video in studio if user actually typed custom text
        if (currentItem) {
            if (userTypedText) {
                const activeCues = parseSubtitlesText(userTypedText, duration);
                currentItem.customCues = activeCues;
                currentItem.hasUserEditedSubtitles = true;
                currentItem.customFormattedText = userTypedText;
            } else if (currentItem.transcription && currentItem.transcription.has_speech) {
                currentItem.hasUserEditedSubtitles = false;
            } else {
                // Silent video with no custom user text -> zero captions!
                currentItem.customCues = [];
                currentItem.hasUserEditedSubtitles = false;
            }
        }

        // Capture user-chosen caption style template, quality, and download format
        const chosenStyle = captionState.style || 'classic';
        const chosenFontScale = captionState.fontScale || 0.052;
        const chosenLineHeight = captionState.lineHeight || 1.16;
        const chosenPosY = (captionState.posY !== undefined) ? captionState.posY : 0.07;
        const chosenQuality = state.selectedQuality || bulkChosenQuality || '1080';
        const chosenFormat = bulkDownloadFormat || 'single';
        const qLabel = chosenQuality;
        const qName = (qLabel === '4k') ? '4K Ultra HD' : ((qLabel === '720') ? '720p HD' : ((qLabel === 'original') ? 'Original' : '1080p FHD'));

        if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = true;
        if (sourceVideo) sourceVideo.pause();

        // Transition back to Bulk Processing Queue card so user watches each video's progress line complete
        state.isBulkStudioMode = false;
        document.body.classList.remove('studio-view-active');
        if (previewActionCard) previewActionCard.classList.add('hidden');
        if (studioBulkFormatBar) studioBulkFormatBar.classList.add('hidden');
        if (btnCaptionEditText) btnCaptionEditText.textContent = '⬇ Download';
        if (processingModal) processingModal.classList.add('hidden');
        if (bulkQueueCard) bulkQueueCard.classList.remove('hidden');
        if (heroSection) heroSection.classList.add('collapsed');
        renderBulkQueue();

        const totalItems = bulkQueue.length;

        if (bulkSummaryBar) bulkSummaryBar.classList.remove('hidden');
        if (bulkSummaryBadge) {
            bulkSummaryBadge.textContent = '⚡ ACTIVE BATCH ENGINE';
            bulkSummaryBadge.style.background = '';
            bulkSummaryBadge.style.color = '';
            bulkSummaryBadge.style.borderColor = '';
        }
        if (bulkSummaryDownloadArea) bulkSummaryDownloadArea.classList.add('hidden');
        if (bulkMasterFill) bulkMasterFill.style.width = '0%';

        isBulkProcessing = true;
        isBulkBatchAborted = false;
        if (btnStopBulkBatch) {
            btnStopBulkBatch.disabled = false;
            btnStopBulkBatch.classList.add('is-active');
        }
        const completedTaskIds = [];

        for (let i = 0; i < totalItems; i++) {
            if (isBulkBatchAborted) break;
            const item = bulkQueue[i];
            item.status = 'processing';
            item.percent = 10;
            updateBulkItemRow(item);

            if (bulkSummaryTitle) {
                bulkSummaryTitle.textContent = `Processing Video ${i + 1} of ${totalItems}: ${item.name} [${qName}]...`;
            }
            if (bulkSummaryStats) {
                bulkSummaryStats.textContent = `Completed ${completedTaskIds.length} of ${totalItems}`;
            }
            if (bulkMasterFill) {
                bulkMasterFill.style.width = `${Math.round((i / totalItems) * 100)}%`;
            }

            try {
                // 1. Ensure video is uploaded to server
                let serverFilename = item.serverFilename;
                if (!serverFilename) {
                    const fd = new FormData();
                    fd.append('video', item.file);
                    if (!captionState.isCaptionAddActive) {
                        fd.append('skip_transcription', 'true');
                    }
                    fd.append('skip_preclean', 'true');
                    const upRes = await fetch('/api/upload', { method: 'POST', body: fd });
                    const upData = await upRes.json();
                    if (!upData.success) throw new Error(upData.error || 'Upload failed');
                    serverFilename = upData.filename;
                    item.serverFilename = serverFilename;
                    if (upData.transcription) item.transcription = upData.transcription;
                } else if (captionState.isCaptionAddActive && !item.transcription && !item.hasUserEditedSubtitles) {
                    try {
                        const trRes = await fetch('/api/transcribe', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ filename: serverFilename })
                        });
                        if (trRes.ok) {
                            const trData = await trRes.json();
                            if (trData.success) item.transcription = trData;
                        }
                    } catch (te) {
                        console.warn('Transcription fetch warning:', te);
                    }
                }

                if (isBulkBatchAborted) {
                    item.status = 'stopped';
                    updateBulkItemRow(item);
                    break;
                }

                item.percent = 20;
                updateBulkItemRow(item);

                // 2. Determine per-video cues:
                // CRITICAL USER REQUIREMENT:
                // 1. User custom cues for this video > 2. This video's OWN speech transcription > 3. EMPTY
                // NEVER fall back to dummy English cues! If no speech, NO subtitles added!
                let videoCues = [];
                if (item.hasUserEditedSubtitles && item.customCues && item.customCues.length > 0) {
                    videoCues = item.customCues;
                } else if (captionState.isCaptionAddActive && item.transcription && item.transcription.has_speech && item.transcription.cues && item.transcription.cues.length > 0) {
                    videoCues = item.transcription.cues;
                } else {
                    videoCues = [];
                }

                const shouldAddCaptions = captionState.isCaptionAddActive && (videoCues && videoCues.length > 0);

                const procRes = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: serverFilename,
                        original_name: item.name || (item.file ? item.file.name : serverFilename),
                        remove_watermark: captionState.isWatermarkRemoveActive,
                        add_captions: shouldAddCaptions,
                        captions: videoCues,
                        caption_style: chosenStyle,
                        caption_size: chosenFontScale,
                        caption_line_height: chosenLineHeight,
                        caption_pos_y: chosenPosY,
                        quality: qLabel
                    })
                });
                const procData = await procRes.json();
                if (!procData.success) throw new Error(procData.error || 'Failed to start');

                const taskId = procData.task_id;
                item.taskId = taskId;

                // 3. Poll until this item completes, updating that video's individual progress line
                await new Promise((resolve, reject) => {
                    const pollInterval = setInterval(async () => {
                        try {
                            if (isBulkBatchAborted) {
                                clearInterval(pollInterval);
                                item.status = 'stopped';
                                updateBulkItemRow(item);
                                resolve();
                                return;
                            }

                            const statusRes = await fetch(`/api/status/${taskId}`);
                            if (!statusRes.ok) return;
                            const statusData = await statusRes.json();

                            if (statusData.status === 'completed') {
                                clearInterval(pollInterval);
                                completedTaskIds.push(taskId);
                                item.status = 'completed';
                                item.percent = 100;
                                item.taskId = taskId;
                                item.downloadUrl = `/api/download/${taskId}?quality=${qLabel}`;
                                updateBulkItemRow(item);

                                // User requirement: If single video download selected, auto-download each video as soon as it finishes!
                                if (chosenFormat === 'single') {
                                    triggerSingleVideoDownload(item, qLabel);
                                }
                                resolve();
                            } else if (statusData.status === 'error') {
                                clearInterval(pollInterval);
                                item.status = 'error';
                                updateBulkItemRow(item);
                                reject(new Error(statusData.error || 'Render failed'));
                            } else {
                                const itemPct = statusData.percent || 0;
                                item.percent = Math.max(18, Math.min(99, Math.round(18 + (itemPct * 0.8))));
                                updateBulkItemRow(item);

                                const currentOverall = Math.min(99, Math.round(((i + (itemPct / 100)) / totalItems) * 100));
                                if (bulkMasterFill) bulkMasterFill.style.width = `${currentOverall}%`;
                            }
                        } catch (e) {
                            clearInterval(pollInterval);
                            reject(e);
                        }
                    }, 350);
                });
            } catch (err) {
                console.error(`Error processing batch video ${i + 1}:`, err);
                item.status = 'error';
                updateBulkItemRow(item);
            }
        }

        isBulkProcessing = false;
        if (btnStopBulkBatch) {
            btnStopBulkBatch.disabled = true;
            btnStopBulkBatch.classList.remove('is-active');
        }
        if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = false;

        if (!isBulkBatchAborted) {
            // Update overall summary bar on completion
            if (bulkSummaryTitle) {
                bulkSummaryTitle.textContent = `🎉 All ${completedTaskIds.length} Videos Completed! [${qName}]`;
            }
            if (bulkSummaryStats) {
                bulkSummaryStats.textContent = `Completed ${completedTaskIds.length} of ${totalItems} (100%)`;
            }
            if (bulkMasterFill) {
                bulkMasterFill.style.width = '100%';
            }
            if (bulkSummaryDownloadArea) {
                bulkSummaryDownloadArea.classList.remove('hidden');
            }

            // User requirement: "and fir jo dawnload setting di he like qullity and zip ya fir singel single us hisab se video dawnload krne he"
            if (completedTaskIds.length > 0) {
                if (chosenFormat === 'zip') {
                    if (bulkSummaryTitle) bulkSummaryTitle.textContent = `📦 Downloading ZIP Archive (${completedTaskIds.length} Videos)...`;
                    if (bulkDockStatusText) bulkDockStatusText.textContent = '📦 Downloading your ZIP archive to device...';
                    await triggerBatchZipDownload(completedTaskIds, qLabel);
                    showBulkAllDoneModal(completedTaskIds.length, qName, completedTaskIds, qLabel, 'zip');
                } else {
                    showBulkAllDoneModal(completedTaskIds.length, qName, completedTaskIds, qLabel, 'single');
                }
            } else {
                showBulkAllDoneModal(completedTaskIds.length, qName, completedTaskIds, qLabel, chosenFormat);
            }
        }
    }

    // Cancel / Close Processing Modal Handler (User can click ✕ on processing modal)
    const btnCloseProcessingModal = document.getElementById('btnCloseProcessingModal');
    if (btnCloseProcessingModal) {
        btnCloseProcessingModal.addEventListener('click', () => {
            if (state.pollInterval) {
                clearInterval(state.pollInterval);
                state.pollInterval = null;
            }
            if (processingModal) processingModal.classList.add('hidden');
            if (previewActionCard) previewActionCard.classList.remove('hidden');
            if (btnCaptionEditCombined) btnCaptionEditCombined.disabled = false;
            if (btnStartAutoProcess) btnStartAutoProcess.disabled = false;
            if (btnStartBulkProcess) btnStartBulkProcess.disabled = false;
            if (removerBtnText) removerBtnText.textContent = 'Remover';
            isBulkProcessing = false;
            console.log('Processing modal closed by user.');
        });
    }

    // --- BULK READY MODAL POPUP HANDLERS ---
    function showBulkReadyModal(count) {
        if (!bulkUploadCompleteModal) return;
        if (bulkReadyModalCount) {
            bulkReadyModalCount.textContent = `${count} Video${count > 1 ? 's' : ''}`;
        }
        bulkUploadCompleteModal.classList.remove('hidden');
    }

    function closeBulkReadyModal() {
        if (!bulkUploadCompleteModal) return;
        bulkUploadCompleteModal.classList.add('hidden');
    }

    if (btnCloseBulkReadyModal) {
        btnCloseBulkReadyModal.addEventListener('click', closeBulkReadyModal);
    }

    // Option 1: ✨ Yes, Generate Captions -> Automatically activates captions and opens Studio Layout with First Video
    if (btnModalBulkSetupCaptions) {
        btnModalBulkSetupCaptions.addEventListener('click', () => {
            closeBulkReadyModal();
            captionState.isCaptionAddActive = true;
            captionState.isWatermarkRemoveActive = true;
            updateFeatureTogglesUI();
            openBulkStudioWithFirstVideo();
        });
    }

    // Option 2: No, Just Remove Watermarks (Fast) -> Runs fast watermark removal
    if (btnModalBulkQuickClean) {
        btnModalBulkQuickClean.addEventListener('click', () => {
            closeBulkReadyModal();
            startBulkProcessing();
        });
    }

    // Back to Upload button is unified in returnToUpload()

    // Watermark Studio Panel Action Button (Processes in chosen quality & downloads)
    const btnWmCombinedAction = document.getElementById('btnWmCombinedAction');
    if (btnWmCombinedAction) {
        btnWmCombinedAction.addEventListener('click', () => {
            if (state.isBulkStudioMode) {
                executeBulkStudioBatchProcessing();
            } else {
                executeProcessing({ remove_watermark: true, add_captions: false });
            }
        });
    }

    if (bulkUploadCompleteModal) {
        bulkUploadCompleteModal.addEventListener('click', (e) => {
            if (e.target === bulkUploadCompleteModal) {
                closeBulkReadyModal();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeBulkReadyModal();
            const contactModal = document.getElementById('contactModal');
            const privacyModal = document.getElementById('privacyModal');
            const termsModal = document.getElementById('termsModal');
            if (contactModal) contactModal.classList.add('hidden');
            if (privacyModal) privacyModal.classList.add('hidden');
            if (termsModal) termsModal.classList.add('hidden');
        }
    });

    // --- FAQ ACCORDION HANDLERS ---
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.closest('.faq-item');
            if (!item) return;
            const wasActive = item.classList.contains('active');
            
            // Close other items
            document.querySelectorAll('.faq-item').forEach(other => {
                other.classList.remove('active');
            });

            // Toggle clicked item
            if (!wasActive) {
                item.classList.add('active');
            }
        });
    });

    // --- CONTACT & LEGAL MODALS HANDLERS ---
    const contactModal = document.getElementById('contactModal');
    const privacyModal = document.getElementById('privacyModal');
    const termsModal = document.getElementById('termsModal');

    const btnOpenContactModal = document.getElementById('btnOpenContactModal');
    const btnOpenSupportModal = document.getElementById('btnOpenSupportModal');
    const btnCloseContactModal = document.getElementById('btnCloseContactModal');

    const btnOpenPrivacyModal = document.getElementById('btnOpenPrivacyModal');
    const btnClosePrivacyModal = document.getElementById('btnClosePrivacyModal');

    const btnOpenTermsModal = document.getElementById('btnOpenTermsModal');
    const btnCloseTermsModal = document.getElementById('btnCloseTermsModal');

    if (btnOpenContactModal && contactModal) {
        btnOpenContactModal.addEventListener('click', () => contactModal.classList.remove('hidden'));
    }
    if (btnOpenSupportModal && contactModal) {
        btnOpenSupportModal.addEventListener('click', () => contactModal.classList.remove('hidden'));
    }
    if (btnCloseContactModal && contactModal) {
        btnCloseContactModal.addEventListener('click', () => contactModal.classList.add('hidden'));
    }

    if (btnOpenPrivacyModal && privacyModal) {
        btnOpenPrivacyModal.addEventListener('click', () => privacyModal.classList.remove('hidden'));
    }
    if (btnClosePrivacyModal && privacyModal) {
        btnClosePrivacyModal.addEventListener('click', () => privacyModal.classList.add('hidden'));
    }

    if (btnOpenTermsModal && termsModal) {
        btnOpenTermsModal.addEventListener('click', () => termsModal.classList.remove('hidden'));
    }
    if (btnCloseTermsModal && termsModal) {
        btnCloseTermsModal.addEventListener('click', () => termsModal.classList.add('hidden'));
    }

    [contactModal, privacyModal, termsModal].forEach(m => {
        if (m) {
            m.addEventListener('click', (e) => {
                if (e.target === m) m.classList.add('hidden');
            });
        }
    });

    function renderCuesList() {
        // Cues are rendered live via live-caption-overlay and captionTextInput
    }

    // Initialize Dola Edits features
    updateFeatureTogglesUI();
});
