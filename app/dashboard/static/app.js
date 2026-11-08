/**

 * stylesdays pSEO Static Site Generator & Management Dashboard SPA Client

 */



(function () {

  'use strict';



  // State Management

  const state = {

    config: {},

    status: {},

    posts: [],

    selectedPostSlug: null,

    previewDebounceTimer: null,

    logPollInterval: null,

    activePlatform: 'cloudflare',

    activeTab: 'tab-ingest',

    projects: [],

    activeProject: 'stylesdays',

  };

  const State = state; // Safe alias preventing ReferenceError: State is not defined



  // DOM Elements

  const DOM = {

    tabs: document.querySelectorAll('.tab-btn'),

    panes: document.querySelectorAll('.tab-pane'),

    selectedPlatformBadge: document.getElementById('selectedPlatformBadge'),
    selectedPlatformIcon: document.getElementById('selectedPlatformIcon'),
    selectedPlatformText: document.getElementById('selectedPlatformText'),

    selectActiveProject: document.getElementById('selectActiveProject'),
    btnNewProject: document.getElementById('btnNewProject'),
    modalNewProject: document.getElementById('modalNewProject'),
    btnCloseNewProjectModal: document.getElementById('btnCloseNewProjectModal'),
    btnCancelNewProject: document.getElementById('btnCancelNewProject'),
    newProjectForm: document.getElementById('newProjectForm'),
    newProjName: document.getElementById('newProjName'),
    newProjPlatform: document.getElementById('newProjPlatform'),
    newProjCfWorker: document.getElementById('newProjCfWorker'),
    newProjCfDomain: document.getElementById('newProjCfDomain'),
    newProjGhOwner: document.getElementById('newProjGhOwner'),
    newProjGhRepo: document.getElementById('newProjGhRepo'),
    newProjSitemapUrl: document.getElementById('newProjSitemapUrl'),
    cfgStep1GithubOwner: document.getElementById('cfgStep1GithubOwner'),
    cfgStep1GithubRepo: document.getElementById('cfgStep1GithubRepo'),
    cfgStep1GithubAccount: document.getElementById('cfgStep1GithubAccount'),
    btnRefreshStep1Orgs: document.getElementById('btnRefreshStep1Orgs'),
    cfgStep1AutoRootOrg: document.getElementById('cfgStep1AutoRootOrg'),
    btnStep1CheckOrg: document.getElementById('btnStep1CheckOrg'),
    btnStep1CreateRepo: document.getElementById('btnStep1CreateRepo'),
    linkStep1OpenGithubOrg: document.getElementById('linkStep1OpenGithubOrg'),
    step1RootDomainPreview: document.getElementById('step1RootDomainPreview'),
    step1OrgStatusFeedback: document.getElementById('step1OrgStatusFeedback'),
    step1GithubTokenDetectedBadge: document.getElementById('step1GithubTokenDetectedBadge'),
    step1TargetCadreCf: document.getElementById('step1TargetCadreCf'),
    step1TargetCadreGh: document.getElementById('step1TargetCadreGh'),
    btnStep1TargetCf: document.getElementById('btnStep1TargetCf'),
    btnStep1TargetGh: document.getElementById('btnStep1TargetGh'),
    step1CfStatusBadge: document.getElementById('step1CfStatusBadge'),
    step1ActivePlatformTitle: document.getElementById('step1ActivePlatformTitle'),
    newProjGhOwnerSelect: document.getElementById('newProjGhOwnerSelect'),
    btnVerifyGhToken: document.getElementById('btnVerifyGhToken'),
    ghStatusFeedback: document.getElementById('ghStatusFeedback'),



    // Stats

    statTotalPosts: document.getElementById('statTotalPosts'),

    statProjectAssets: document.getElementById('statProjectAssets'),

    statNewPosts: document.getElementById('statNewPosts'),

    statUpdatedPosts: document.getElementById('statUpdatedPosts'),

    statCustomPosts: document.getElementById('statCustomPosts'),

    statTheme: document.getElementById('statTheme'),

    gitStatusText: document.getElementById('gitStatusText'),

    gitStatusBadge: document.getElementById('gitStatusBadge'),

    cfStatusText: document.getElementById('cfStatusText'),

    cfStatusBadge: document.getElementById('cfStatusBadge'),



    // Subtabs

    subtabBtns: document.querySelectorAll('.subtab-btn'),

    subtabPanes: document.querySelectorAll('.subtab-content'),



    // Cloudflare Settings

    cloudflareSettingsForm: document.getElementById('cloudflareSettingsForm'),

    cfgCfToken: document.getElementById('cfgCfToken'),

    cfTokenStatusBadge: document.getElementById('cfTokenStatusBadge'),

    toggleCfTokenEye: document.getElementById('toggleCfTokenEye'),

    toggleGhTokenEye: document.getElementById('toggleGhTokenEye'),

    cfgCfAccountId: document.getElementById('cfgCfAccountId'),

    cfgCfAccountSubdomain: document.getElementById('cfgCfAccountSubdomain'),

    cfgCfProjectName: document.getElementById('cfgCfProjectName'),

    cfgCfDeployType: document.getElementById('cfgCfDeployType'),

    cfgCfCustomDomain: document.getElementById('cfgCfCustomDomain'),

    cfgCfCompatibilityDate: document.getElementById('cfgCfCompatibilityDate'),

    cfLiveUrlPreview: document.getElementById('cfLiveUrlPreview'),

    btnVerifyCfToken: document.getElementById('btnVerifyCfToken'),

    cfStatusFeedback: document.getElementById('cfStatusFeedback'),

    optimizeWebpBtn: document.getElementById('optimizeWebpBtn'),

    syncAssetsSettingsBtn: document.getElementById('syncAssetsSettingsBtn'),



    // Settings (GitHub)

    settingsForm: document.getElementById('settingsForm'),

    cfgGithubToken: document.getElementById('cfgGithubToken'),

    tokenStatusBadge: document.getElementById('tokenStatusBadge'),

    selectGithubAccount: document.getElementById('selectGithubAccount'),

    btnRefreshOrgs: document.getElementById('btnRefreshOrgs'),

    cfgGithubOwner: document.getElementById('cfgGithubOwner'),

    cfgAutoRootOrg: document.getElementById('cfgAutoRootOrg'),

    btnCheckCreateOrg: document.getElementById('btnCheckCreateOrg'),

    btnCreateRepoNow: document.getElementById('btnCreateRepoNow'),

    linkOpenGithubOrg: document.getElementById('linkOpenGithubOrg'),

    orgStatusFeedback: document.getElementById('orgStatusFeedback'),

    rootDomainPreview: document.getElementById('rootDomainPreview'),

    cfgGithubRepo: document.getElementById('cfgGithubRepo'),

    cfgGithubBranch: document.getElementById('cfgGithubBranch'),

    cfgGithubIsOrg: document.getElementById('cfgGithubIsOrg'),

    cfgGithubBasePath: document.getElementById('cfgGithubBasePath'),



    buildOptionsForm: document.getElementById('buildOptionsForm'),

    cfgTheme: document.getElementById('cfgTheme'),

    cfgRoutingMode: document.getElementById('cfgRoutingMode'),

    cfgOutputDir: document.getElementById('cfgOutputDir'),

    cfgWpApiUrl: document.getElementById('cfgWpApiUrl'),

    cfgBrandName: document.getElementById('cfgBrandName'),

    cfgBrandTagline: document.getElementById('cfgBrandTagline'),

    cfgAuthorName: document.getElementById('cfgAuthorName'),

    cfgAuthorBio: document.getElementById('cfgAuthorBio'),

    logoStatusBadge: document.getElementById('logoStatusBadge'),

    logoPreviewBox: document.getElementById('logoPreviewBox'),

    logoFilenameText: document.getElementById('logoFilenameText'),

    logoFileInput: document.getElementById('logoFileInput'),

    btnResetLogo: document.getElementById('btnResetLogo'),

    quickLogoPreviewBox: document.getElementById('quickLogoPreviewBox'),

    quickLogoStatusBadge: document.getElementById('quickLogoStatusBadge'),

    quickBrandNameDisplay: document.getElementById('quickBrandNameDisplay'),

    quickTaglineDisplay: document.getElementById('quickTaglineDisplay'),

    quickLogoFileInput: document.getElementById('quickLogoFileInput'),

    quickBtnResetLogo: document.getElementById('quickBtnResetLogo'),

    previewLogoBox: document.getElementById('previewLogoBox'),

    previewLogoStatusBadge: document.getElementById('previewLogoStatusBadge'),

    previewBrandNameDisplay: document.getElementById('previewBrandNameDisplay'),

    previewLogoFilename: document.getElementById('previewLogoFilename'),

    previewLogoFileInput: document.getElementById('previewLogoFileInput'),

    previewBtnResetLogo: document.getElementById('previewBtnResetLogo'),

    cfgEnableToc: document.getElementById('cfgEnableToc'),

    cfgEnableFaq: document.getElementById('cfgEnableFaq'),

    cfgEnableEeat: document.getElementById('cfgEnableEeat'),



    // Ingestion

    ingestionForm: document.getElementById('ingestionForm'),

    ingestSourceType: document.getElementById('ingestSourceType'),

    groupSitemapUrl: document.getElementById('groupSitemapUrl'),

    groupUrlList: document.getElementById('groupUrlList'),

    ingestSitemapUrl: document.getElementById('ingestSitemapUrl'),

    ingestUrlList: document.getElementById('ingestUrlList'),

    ingestMaxPosts: document.getElementById('ingestMaxPosts'),

    ingestDownloadImages: document.getElementById('ingestDownloadImages'),

    ingestForceResync: document.getElementById('ingestForceResync'),

    scanSitemapBtn: document.getElementById('scanSitemapBtn'),

    startIngestBtn: document.getElementById('startIngestBtn'),

    syncAssetsBtn: document.getElementById('syncAssetsBtn'),

    syncAssetsDeployBtn: document.getElementById('syncAssetsDeployBtn'),

    diffResultsBox: document.getElementById('diffResultsBox'),

    diffNewCount: document.getElementById('diffNewCount'),

    diffUpdatedCount: document.getElementById('diffUpdatedCount'),

    diffSyncedCount: document.getElementById('diffSyncedCount'),

    diffSummaryTableBody: document.querySelector('#diffSummaryTable tbody'),



    // Posts Catalog

    postsCatalogBody: document.getElementById('postsCatalogBody'),

    postSearchInput: document.getElementById('postSearchInput'),

    postCategoryFilter: document.getElementById('postCategoryFilter'),

    postStatusFilter: document.getElementById('postStatusFilter'),



    // Modal Editor

    postEditModal: document.getElementById('postEditModal'),

    modalPostSlugTitle: document.getElementById('modalPostSlugTitle'),

    editPostForm: document.getElementById('editPostForm'),

    editPostSlug: document.getElementById('editPostSlug'),

    editPostTitle: document.getElementById('editPostTitle'),

    editPostExcerpt: document.getElementById('editPostExcerpt'),

    editPostCategory: document.getElementById('editPostCategory'),

    editPostParentSlug: document.getElementById('editPostParentSlug'),

    editTakeawaysContainer: document.getElementById('editTakeawaysContainer'),

    editChecklistContainer: document.getElementById('editChecklistContainer'),

    addTakeawayBtn: document.getElementById('addTakeawayBtn'),

    addChecklistBtn: document.getElementById('addChecklistBtn'),

    closeModalBtn: document.getElementById('closeModalBtn'),

    cancelEditBtn: document.getElementById('cancelEditBtn'),



    // Preview

    previewPostSelect: document.getElementById('previewPostSelect'),

    previewThemeSelect: document.getElementById('previewThemeSelect'),

    previewRoutingSelect: document.getElementById('previewRoutingSelect'),

    previewLiveTitle: document.getElementById('previewLiveTitle'),

    previewLiveExcerpt: document.getElementById('previewLiveExcerpt'),

    refreshPreviewBtn: document.getElementById('refreshPreviewBtn'),

    previewIframe: document.getElementById('previewIframe'),

    viewportBtns: document.querySelectorAll('.viewport-btn'),

    modelSwitcherBar: document.getElementById('modelSwitcherBar'),

    modelPreviewBtns: document.querySelectorAll('.model-preview-btn'),



    // Theme & Routing Visual Gallery

    btnOpenThemePreview: document.getElementById('btnOpenThemePreview'),

    templatePreviewModal: document.getElementById('templatePreviewModal'),

    closeTemplateModalBtn: document.getElementById('closeTemplateModalBtn'),

    templateModalIframe: document.getElementById('templateModalIframe'),

    templateModalThemeBadge: document.getElementById('templateModalThemeBadge'),

    templateModalRoutingBadge: document.getElementById('templateModalRoutingBadge'),

    applyTemplateThemeBtn: document.getElementById('applyTemplateThemeBtn'),



    // Build & Deploy Cockpit

    quickBuildBtn: document.getElementById('quickBuildBtn'),

    triggerBuildBtn: document.getElementById('triggerBuildBtn'),

    triggerDeployBtn: document.getElementById('triggerDeployBtn'),

    deployDryRun: document.getElementById('deployDryRun'),

    triggerCfDeployBtn: document.getElementById('triggerCfDeployBtn'),

    deployCfDryRun: document.getElementById('deployCfDryRun'),

    triggerDualDeployBtn: document.getElementById('triggerDualDeployBtn'),

    cockpitCfWorker: document.getElementById('cockpitCfWorker'),

    cockpitCfSubdomain: document.getElementById('cockpitCfSubdomain'),

    cockpitCfUrlLink: document.getElementById('cockpitCfUrlLink'),

    cockpitGhRepo: document.getElementById('cockpitGhRepo'),

    cockpitGhUrlLink: document.getElementById('cockpitGhUrlLink'),

    cockpitOutputDir: document.getElementById('cockpitOutputDir'),

    cockpitTheme: document.getElementById('cockpitTheme'),

    copyLogsBtn: document.getElementById('copyLogsBtn'),

    termFilterBtns: document.querySelectorAll('.term-filter-btn'),

    terminalBody: document.getElementById('terminalBody'),

    clearLogsBtn: document.getElementById('clearLogsBtn'),



    // Platform Division & Stepper Elements

    platformSelectCf: document.getElementById('platformSelectCf'),

    platformSelectGh: document.getElementById('platformSelectGh'),

    platformSelectDual: document.getElementById('platformSelectDual'),
    platformSelectSplit: document.getElementById('platformSelectSplit'),
    toggleTerminalSizeBtn: document.getElementById('toggleTerminalSizeBtn'),
    terminalSection: document.getElementById('terminalSection'),
    splitCfWorkerName: document.getElementById('splitCfWorkerName'),
    splitGhRepoName: document.getElementById('splitGhRepoName'),

    // Platform Settings Modal Elements
    btnOpenSettings: document.getElementById('btnOpenSettings'),
    btnCloseSettingsModal: document.getElementById('btnCloseSettingsModal'),
    platformSettingsModal: document.getElementById('platformSettingsModal'),
    modalTabBtnCf: document.getElementById('modalTabBtnCf'),
    modalTabBtnGh: document.getElementById('modalTabBtnGh'),
    settingsPaneCf: document.getElementById('settingsPaneCf'),
    settingsPaneGh: document.getElementById('settingsPaneGh'),

    stepCardIngest: document.getElementById('stepCardIngest'),

    stepCardThemes: document.getElementById('stepCardThemes'),

    stepCardPosts: document.getElementById('stepCardPosts'),

    stepCardPlatform: document.getElementById('stepCardPlatform'),

    stepCardDeploy: document.getElementById('stepCardDeploy'),

    stepPlatformBadge: document.getElementById('stepPlatformBadge'),

    stepPlatformTitle: document.getElementById('stepPlatformTitle'),

    stepPlatformDesc: document.getElementById('stepPlatformDesc'),

    statTargetUrl: document.getElementById('statTargetUrl'),

    statPlatformCard: document.getElementById('statPlatformCard'),

    heroCfDeployBtn: document.getElementById('heroCfDeployBtn'),

    heroGhDeployBtn: document.getElementById('heroGhDeployBtn'),

    triggerBuildGhBtn: document.getElementById('triggerBuildGhBtn'),

    cockpitGhBranch: document.getElementById('cockpitGhBranch'),

    // Single-Cadre View & Dedicated Platform Workspaces
    workspaceCloudflare: document.getElementById('workspaceCloudflare'),
    workspaceGithub: document.getElementById('workspaceGithub'),
    tabBtnCloudflare: document.getElementById('tabBtnCloudflare'),
    tabBtnGithub: document.getElementById('tabBtnGithub'),
    viewToggleCf: document.getElementById('viewToggleCf'),
    viewToggleGh: document.getElementById('viewToggleGh'),
    viewToggleBoth: document.getElementById('viewToggleBoth'),
    deployCockpitGrid: document.getElementById('deployCockpitGrid'),
    cockpitCardCf: document.getElementById('cockpitCardCf'),
    cockpitCardGh: document.getElementById('cockpitCardGh'),

    toastContainer: document.getElementById('toastContainer'),

  };



  // Toast Utilities

  function showToast(message, type = 'info') {

    const toast = document.createElement('div');

    toast.className = `toast ${type}`;

    toast.textContent = message;

    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {

      toast.style.opacity = '0';

      toast.style.transition = 'opacity 0.3s ease';

      setTimeout(() => toast.remove(), 300);

    }, 4000);

  }



  function appendTerminalLog(msg, type = 'info') {

    if (!DOM.terminalBody) return;

    const line = document.createElement('div');

    line.className = `log-${type}`;

    line.textContent = msg;

    DOM.terminalBody.appendChild(line);

    DOM.terminalBody.scrollTop = DOM.terminalBody.scrollHeight;

  }



  // API Call Wrapper

  async function api(endpoint, method = 'GET', data = null) {

    const opts = {

      method,

      headers: { 'Content-Type': 'application/json' },

    };

    if (data && (method === 'POST' || method === 'PUT')) {

      opts.body = JSON.stringify(data);

    }

    const res = await fetch(endpoint, opts);

    if (!res.ok) {

      let errText = res.statusText;

      try {

        const errJson = await res.json();

        errText = errJson.error || errText;

      } catch (e) {}

      throw new Error(errText);

    }

    return res.json();

  }



  // Active platform state: 'cloudflare' | 'github' | 'dual'

  let currentPlatformMode = 'cloudflare';



  function updateStepperActive(tabTarget) {
    const stepCards = [DOM.stepCardIngest, DOM.stepCardThemes, DOM.stepCardPosts, DOM.stepCardPlatform, DOM.stepCardDeploy];
    stepCards.forEach((c) => {
      if (c) {
        c.classList.remove('active');
        const badge = c.querySelector('.step-badge');
        if (badge) badge.classList.remove('active-badge');
      }
    });

    let activeCard = null;
    if (tabTarget === 'tab-ingest') {
      activeCard = DOM.stepCardIngest;
    } else if (tabTarget === 'tab-themes') {
      activeCard = DOM.stepCardThemes;
    } else if (tabTarget === 'tab-posts') {
      activeCard = DOM.stepCardPosts;
    } else if (tabTarget === 'tab-deploy' || tabTarget === 'tab-preview' || tabTarget === 'tab-cloudflare' || tabTarget === 'tab-github' || tabTarget === 'tab-split') {
      activeCard = DOM.stepCardDeploy;
    }

    if (activeCard) {
      activeCard.classList.add('active');
      const badge = activeCard.querySelector('.step-badge');
      if (badge) badge.classList.add('active-badge');
    }
  }



  function openPlatformSettings(tab) {
    if (!tab) tab = (typeof currentPlatformMode !== 'undefined' && currentPlatformMode === 'github') ? 'github' : 'cloudflare';

    if (!DOM.platformSettingsModal) return;

    DOM.platformSettingsModal.classList.add('active');

    DOM.platformSettingsModal.style.display = 'flex';

    switchSettingsModalTab(tab);

    document.body.style.overflow = 'hidden';

  }



  function closePlatformSettings() {

    if (!DOM.platformSettingsModal) return;

    DOM.platformSettingsModal.classList.remove('active');

    DOM.platformSettingsModal.style.display = 'none';

    document.body.style.overflow = '';

  }



  function switchSettingsModalTab(tab) {

    if (tab === 'github') {

      if (DOM.modalTabBtnGh) DOM.modalTabBtnGh.classList.add('active', 'gh');

      if (DOM.modalTabBtnCf) DOM.modalTabBtnCf.classList.remove('active', 'cf');

      if (DOM.settingsPaneGh) DOM.settingsPaneGh.style.display = 'block';

      if (DOM.settingsPaneCf) DOM.settingsPaneCf.style.display = 'none';

    } else {

      if (DOM.modalTabBtnCf) DOM.modalTabBtnCf.classList.add('active', 'cf');

      if (DOM.modalTabBtnGh) DOM.modalTabBtnGh.classList.remove('active', 'gh');

      if (DOM.settingsPaneCf) DOM.settingsPaneCf.style.display = 'block';

      if (DOM.settingsPaneGh) DOM.settingsPaneGh.style.display = 'none';

    }

  }



  window.openPlatformSettings = openPlatformSettings;

  window.closePlatformSettings = closePlatformSettings;

  function setActivePlatformView(view) {
    if (!view) view = 'cf';
    if (view === 'cloudflare') view = 'cf';
    if (view === 'github') view = 'gh';
    if (view === 'dual' || view === 'split') view = 'cf';

    currentPlatformMode = view === 'cf' ? 'cloudflare' : 'github';
    state.activePlatform = currentPlatformMode;

    // 1. Show strictly the selected workspace, hide the other
    const wsCf = document.getElementById('workspaceCloudflare') || DOM.workspaceCloudflare;
    const wsGh = document.getElementById('workspaceGithub') || DOM.workspaceGithub;
    if (wsCf && wsGh) {
      if (view === 'cf') {
        wsCf.style.display = 'flex';
        wsGh.style.display = 'none';
      } else {
        wsGh.style.display = 'flex';
        wsCf.style.display = 'none';
      }
    }

    // 2. Update top nav tabs if tab-deploy is active
    const isDeployActive = DOM.panes && Array.from(DOM.panes).some(p => p.id === 'tab-deploy' && p.classList.contains('active'));
    if (isDeployActive && DOM.tabBtnCloudflare && DOM.tabBtnGithub) {
      if (view === 'cf') {
        DOM.tabBtnCloudflare.classList.add('active');
        DOM.tabBtnGithub.classList.remove('active');
      } else {
        DOM.tabBtnGithub.classList.add('active');
        DOM.tabBtnCloudflare.classList.remove('active');
      }
    }

    // 3. Update hidden compatibility buttons
    const viewBtns = [DOM.viewToggleCf, DOM.viewToggleGh, DOM.viewToggleBoth];
    viewBtns.forEach((btn) => {
      if (btn) {
        if (btn.getAttribute('data-view') === view) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      }
    });

    if (DOM.platformSelectCf) DOM.platformSelectCf.classList.toggle('active', view === 'cf');
    if (DOM.platformSelectGh) DOM.platformSelectGh.classList.toggle('active', view === 'gh');

    // 4. Update target URL preview in top telemetry ribbon
    if (view === 'cf') {
      const cfUrl = computeCloudflareLiveUrl();
      if (DOM.statTargetUrl) {
        DOM.statTargetUrl.textContent = cfUrl + ' ↗';
        DOM.statTargetUrl.href = cfUrl;
      }
      if (DOM.statPlatformCard) DOM.statPlatformCard.style.borderLeftColor = 'var(--accent-cloudflare)';
    } else {
      const ghUrl = (DOM.cockpitGhUrlLink && DOM.cockpitGhUrlLink.href) || 'https://annadeco.github.io';
      if (DOM.statTargetUrl) {
        DOM.statTargetUrl.textContent = ghUrl + ' ↗';
        DOM.statTargetUrl.href = ghUrl;
      }
      if (DOM.statPlatformCard) DOM.statPlatformCard.style.borderLeftColor = 'var(--accent-github)';
    }

    // 5. Synchronize Selected Platform Indicator near Brand Logo
    const selBadge = DOM.selectedPlatformBadge || document.getElementById('selectedPlatformBadge');
    const selIcon = DOM.selectedPlatformIcon || document.getElementById('selectedPlatformIcon');
    const selText = DOM.selectedPlatformText || document.getElementById('selectedPlatformText');
    if (selBadge && selIcon && selText) {
      if (view === 'cf') {
        selBadge.className = 'platform-selected-badge cf';
        selIcon.textContent = '🟧';
        selText.textContent = 'Cloudflare Edge';
      } else {
        selBadge.className = 'platform-selected-badge gh';
        selIcon.textContent = '🐙';
        selText.textContent = 'GitHub Pages';
      }
    }

    // 6. Synchronize Step 1 Ingestion Platform Target Cadres (Strict Isolation)
    const cadreCf = document.getElementById('step1TargetCadreCf') || DOM.step1TargetCadreCf;
    const cadreGh = document.getElementById('step1TargetCadreGh') || DOM.step1TargetCadreGh;
    const btnTargetCf = document.getElementById('btnStep1TargetCf') || DOM.btnStep1TargetCf;
    const btnTargetGh = document.getElementById('btnStep1TargetGh') || DOM.btnStep1TargetGh;

    const titleEl = document.getElementById('step1ActivePlatformTitle') || DOM.step1ActivePlatformTitle;
    if (titleEl) {
      if (view === 'cf') {
        titleEl.textContent = '🌐 Active Deployment Target: Cloudflare Edge';
      } else if (view === 'gh') {
        titleEl.textContent = '🌐 Active Deployment Target: GitHub Pages';
      } else {
        titleEl.textContent = '🌐 Active Deployment Targets (Both Platforms)';
      }
    }

    if (cadreCf && cadreGh) {
      if (view === 'cf') {
        cadreCf.style.display = 'block';
        cadreGh.style.display = 'none';
      } else if (view === 'gh') {
        cadreGh.style.display = 'block';
        cadreCf.style.display = 'none';
      } else {
        cadreCf.style.display = 'block';
        cadreGh.style.display = 'block';
      }
    }

    if (btnTargetCf && btnTargetGh) {
      if (view === 'cf') {
        btnTargetCf.classList.add('active', 'cf');
        btnTargetGh.classList.remove('active', 'gh');
      } else if (view === 'gh') {
        btnTargetGh.classList.add('active', 'gh');
        btnTargetCf.classList.remove('active', 'cf');
      } else {
        btnTargetCf.classList.add('active', 'cf');
        btnTargetGh.classList.add('active', 'gh');
      }
    }
  }

  window.setActivePlatformView = setActivePlatformView;
  window.switchTab = switchTab;

  function switchTab(tabId, platform) {
    state.activeTab = tabId;
    if (platform) state.activePlatform = platform;
    // Map legacy platform tabs to the unified deploy cockpit
    if (tabId === 'tab-cloudflare') {
      tabId = 'tab-deploy';
      if (!platform) platform = 'cloudflare';
    } else if (tabId === 'tab-github') {
      tabId = 'tab-deploy';
      if (!platform) platform = 'github';
    } else if (tabId === 'tab-split') {
      tabId = 'tab-deploy';
      if (!platform) platform = 'cloudflare';
    }

    DOM.tabs.forEach((t) => {
      const tTab = t.getAttribute('data-tab');
      const tPlatform = t.getAttribute('data-platform');
      if (tTab === tabId) {
        if (tabId === 'tab-deploy') {
          if (platform === 'cloudflare' && tPlatform === 'cloudflare') {
            t.classList.add('active');
          } else if (platform === 'github' && tPlatform === 'github') {
            t.classList.add('active');
          } else if (!platform && tPlatform === 'cloudflare') {
            t.classList.add('active');
          } else {
            t.classList.remove('active');
          }
        } else {
          t.classList.add('active');
        }
      } else {
        t.classList.remove('active');
      }
    });

    DOM.panes.forEach((p) => {
      if (p.id === tabId) p.classList.add('active');
      else p.classList.remove('active');
    });

    if (tabId === 'tab-deploy') {
      const view = platform === 'github' ? 'gh' : 'cf';
      setActivePlatformView(view);
    }

    updateStepperActive(tabId);

    if (tabId === 'tab-preview' && state.selectedPostSlug) {
      triggerPreview();
    }
  }

  // Tab Navigation Handling
  // =========================================================================
  // MULTI-PROJECT MANAGEMENT SYSTEM
  // =========================================================================

  async function loadProjects() {
    try {
      const res = await api('/api/projects');
      if (res && res.projects) {
        state.projects = res.projects;
        state.activeProject = res.active_project || 'stylesdays';
        renderProjectSelector();
      }
    } catch (err) {
      console.warn('Could not load projects list:', err);
    }
  }

  function renderProjectSelector() {
    if (!DOM.selectActiveProject) return;
    DOM.selectActiveProject.innerHTML = '';
    state.projects.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p.id;
      const count = p.total_posts || 0;
      opt.textContent = `${p.name || p.id} (${count} posts)`;
      if (p.id === state.activeProject) {
        opt.selected = true;
      }
      DOM.selectActiveProject.appendChild(opt);
    });
  }

  async function switchProject(projectId) {
    if (!projectId || projectId === state.activeProject) return;
    try {
      appendTerminalLog(`[PROJECT] Switching active project to '${projectId}'...`, 'info');
      const res = await api('/api/projects/switch', 'POST', { project_id: projectId });
      state.activeProject = res.active_project || projectId;
      showToast(res.message || `Switched to project ${projectId}`, 'success');
      appendTerminalLog(`[PROJECT] Active project is now '${state.activeProject}' (${res.total_posts} posts, ${res.categories_count} categories).`, 'success');

      // Refresh status, config, posts, and category filter
      await refreshSystem();
      await refreshPosts();
      await loadProjects();
    } catch (err) {
      showToast(`Failed switching project: ${err.message}`, 'error');
      appendTerminalLog(`[PROJECT ERROR] ${err.message}`, 'error');
    }
  }

  function openNewProjectModal() {
    if (!DOM.modalNewProject) return;
    DOM.modalNewProject.style.display = 'flex';
    DOM.modalNewProject.setAttribute('aria-hidden', 'false');
    if (DOM.newProjName) {
      DOM.newProjName.value = '';
      DOM.newProjName.focus();
    }
    if (DOM.newProjCfWorker && DOM.cfgCfProjectName) {
      DOM.newProjCfWorker.value = '';
    }
    if (DOM.newProjGhOwner && DOM.cfgGithubOwner) {
      DOM.newProjGhOwner.value = DOM.cfgGithubOwner.value || '';
    }
    if (DOM.newProjGhRepo) {
      DOM.newProjGhRepo.value = '';
    }
    if (DOM.newProjSitemapUrl) {
      DOM.newProjSitemapUrl.value = '';
    }
  }

  function closeNewProjectModal() {
    if (!DOM.modalNewProject) return;
    DOM.modalNewProject.style.display = 'none';
    DOM.modalNewProject.setAttribute('aria-hidden', 'true');
  }

  async function handleCreateNewProject(e) {
    e.preventDefault();
    const name = (DOM.newProjName && DOM.newProjName.value.trim()) || '';
    if (!name) {
      showToast('Please enter a project name', 'error');
      return;
    }

    const payload = {
      name,
      platform: (DOM.newProjPlatform && DOM.newProjPlatform.value) || 'cloudflare',
      cf_project_name: (DOM.newProjCfWorker && DOM.newProjCfWorker.value.trim()) || '',
      cf_custom_domain: (DOM.newProjCfDomain && DOM.newProjCfDomain.value.trim()) || '',
      gh_owner: (DOM.newProjGhOwner && DOM.newProjGhOwner.value.trim()) || '',
      gh_repo: (DOM.newProjGhRepo && DOM.newProjGhRepo.value.trim()) || '',
      sitemap_url: (DOM.newProjSitemapUrl && DOM.newProjSitemapUrl.value.trim()) || '',
    };

    try {
      appendTerminalLog(`[PROJECT] Creating new isolated project '${name}'...`, 'info');
      const res = await api('/api/projects', 'POST', payload);
      closeNewProjectModal();
      showToast(res.message || `Project '${name}' created with empty categories!`, 'success');
      appendTerminalLog(`[PROJECT] Project '${name}' created. Starting with 0 posts and empty categories.`, 'success');

      // Update active state
      state.activeProject = res.active_project || name.toLowerCase();

      // Clear posts and categories immediately
      state.posts = [];
      populateCategoryFilter();
      renderPostsTable();

      // Refresh all systems
      await refreshSystem();
      await refreshPosts();
      await loadProjects();
    } catch (err) {
      showToast(`Error creating project: ${err.message}`, 'error');
      appendTerminalLog(`[PROJECT ERROR] ${err.message}`, 'error');
    }
  }

  function initProjectSystem() {
    loadProjects();

    if (DOM.selectActiveProject) {
      DOM.selectActiveProject.addEventListener('change', (e) => {
        switchProject(e.target.value);
      });
    }

    if (DOM.btnNewProject) {
      DOM.btnNewProject.addEventListener('click', openNewProjectModal);
    }
    if (DOM.btnCloseNewProjectModal) {
      DOM.btnCloseNewProjectModal.addEventListener('click', closeNewProjectModal);
    }
    if (DOM.btnCancelNewProject) {
      DOM.btnCancelNewProject.addEventListener('click', closeNewProjectModal);
    }
    if (DOM.newProjectForm) {
      DOM.newProjectForm.addEventListener('submit', handleCreateNewProject);
    }

    // Two-way synchronization for Step 1 GitHub inputs
    if (DOM.cfgStep1GithubOwner) {
      DOM.cfgStep1GithubOwner.addEventListener('change', async () => {
        const val = DOM.cfgStep1GithubOwner.value.trim();
        if (DOM.cfgGithubOwner) DOM.cfgGithubOwner.value = val;
        updateRootDomainPreview();
        try {
          await api('/api/config', 'POST', { github: { owner: val } });
          showToast(`GitHub Organization updated to '${val}'`, 'info');
        } catch (e) {
          console.warn('Auto-save of GitHub owner failed:', e);
        }
      });
    }

    if (DOM.cfgStep1GithubRepo) {
      DOM.cfgStep1GithubRepo.addEventListener('change', async () => {
        const val = DOM.cfgStep1GithubRepo.value.trim();
        if (DOM.cfgGithubRepo) DOM.cfgGithubRepo.value = val;
        updateRootDomainPreview();
        try {
          await api('/api/config', 'POST', { github: { repo: val } });
          showToast(`GitHub Repository updated to '${val}'`, 'info');
        } catch (e) {
          console.warn('Auto-save of GitHub repo failed:', e);
        }
      });
    }

    if (DOM.cfgGithubOwner) {
      DOM.cfgGithubOwner.addEventListener('input', () => {
        if (DOM.cfgStep1GithubOwner) DOM.cfgStep1GithubOwner.value = DOM.cfgGithubOwner.value;
      });
    }

    if (DOM.cfgGithubRepo) {
      DOM.cfgGithubRepo.addEventListener('input', () => {
        if (DOM.cfgStep1GithubRepo) DOM.cfgStep1GithubRepo.value = DOM.cfgGithubRepo.value;
      });
    }
  }

  function initTabs() {
    DOM.tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-tab');
        const platform = tab.getAttribute('data-platform');
        switchTab(target, platform);
      });
    });
  }



  function computeCloudflareLiveUrl() {
    const custom = (DOM.cfgCfCustomDomain && DOM.cfgCfCustomDomain.value || '').trim();
    if (custom) {
      return (custom.startsWith('http://') || custom.startsWith('https://')) ? custom : ('https://' + custom.replace(/^\/+/, ''));
    }
    const proj = (DOM.cfgCfProjectName && DOM.cfgCfProjectName.value.trim()) || 'gardenhome';
    const deployType = (DOM.cfgCfDeployType && DOM.cfgCfDeployType.value) || 'workers_assets';
    const subdomain = (DOM.cfgCfAccountSubdomain && DOM.cfgCfAccountSubdomain.value.trim()) || '';
    if (subdomain) {
      return 'https://' + proj + '.' + subdomain + '.workers.dev';
    }
    if (deployType === 'pages') {
      return 'https://' + proj + '.pages.dev';
    }
    return 'https://' + proj + '.workers.dev';
  }

  function updateCloudflareLiveUrlPreview() {
    const url = computeCloudflareLiveUrl();
    if (DOM.cfLiveUrlPreview) {
      DOM.cfLiveUrlPreview.textContent = url;
      DOM.cfLiveUrlPreview.href = url;
    }
    if (DOM.cockpitCfUrlLink) {
      DOM.cockpitCfUrlLink.textContent = url + ' ↗';
      DOM.cockpitCfUrlLink.href = url;
    }
    if (DOM.cockpitCfSubdomain && DOM.cfgCfAccountSubdomain) {
      DOM.cockpitCfSubdomain.textContent = DOM.cfgCfAccountSubdomain.value.trim() || '—';
    }
    if (DOM.cockpitCfWorker && DOM.cfgCfProjectName) {
      DOM.cockpitCfWorker.textContent = DOM.cfgCfProjectName.value.trim() || 'gardenhome';
    }
    if (DOM.splitCfWorkerName) {
      const host = url.replace(/^https?:\/\//, '');
      DOM.splitCfWorkerName.textContent = host;
    }
    if (DOM.statTargetUrl) {
      const isCfActive = currentPlatformMode === 'cloudflare' || (DOM.platformSelectCf && DOM.platformSelectCf.classList.contains('active'));
      if (isCfActive) {
        DOM.statTargetUrl.textContent = url + ' ↗';
        DOM.statTargetUrl.href = url;
      }
    }
    return url;
  }

  function setPlatformMode(mode) {
    if (mode === 'cloudflare') {
      switchTab('tab-deploy', 'cloudflare');
    } else if (mode === 'github') {
      switchTab('tab-deploy', 'github');
    } else if (mode === 'dual' || mode === 'split') {
      switchTab('tab-deploy', 'both');
    }
  }

  function initPlatformDivision() {
    // Header brand platform indicator toggle
    if (DOM.selectedPlatformBadge) {
      DOM.selectedPlatformBadge.addEventListener('click', () => {
        const nextMode = currentPlatformMode === 'cloudflare' ? 'gh' : 'cf';
        setActivePlatformView(nextMode);
      });
    }

    // Step 1 Platform Target Switcher buttons
    const btnStep1Cf = document.getElementById('btnStep1TargetCf') || DOM.btnStep1TargetCf;
    const btnStep1Gh = document.getElementById('btnStep1TargetGh') || DOM.btnStep1TargetGh;
    if (btnStep1Cf) {
      btnStep1Cf.addEventListener('click', () => setActivePlatformView('cf'));
    }
    if (btnStep1Gh) {
      btnStep1Gh.addEventListener('click', () => setActivePlatformView('gh'));
    }

    // Cockpit platform view toggle buttons
    if (DOM.viewToggleCf) {
      DOM.viewToggleCf.addEventListener('click', () => switchTab('tab-deploy', 'cloudflare'));
    }
    if (DOM.viewToggleGh) {
      DOM.viewToggleGh.addEventListener('click', () => switchTab('tab-deploy', 'github'));
    }
    if (DOM.viewToggleBoth) {
      DOM.viewToggleBoth.addEventListener('click', () => setActivePlatformView('both'));
    }

    if (DOM.platformSelectCf) {
      DOM.platformSelectCf.addEventListener('click', () => setPlatformMode('cloudflare'));
    }
    if (DOM.platformSelectGh) {
      DOM.platformSelectGh.addEventListener('click', () => setPlatformMode('github'));
    }
    if (DOM.platformSelectDual) {
      DOM.platformSelectDual.addEventListener('click', () => setPlatformMode('dual'));
    }
    if (DOM.platformSelectSplit) {
      DOM.platformSelectSplit.addEventListener('click', () => setPlatformMode('split'));
    }
    if (DOM.toggleTerminalSizeBtn && DOM.terminalSection) {
      DOM.toggleTerminalSizeBtn.addEventListener('click', () => {
        DOM.terminalSection.classList.toggle('terminal-expanded');
      });
    }

    // Platform Settings Modal Event Listeners
    if (DOM.btnOpenSettings) {
      DOM.btnOpenSettings.addEventListener('click', () => openPlatformSettings());
    }
    if (DOM.btnCloseSettingsModal) {
      DOM.btnCloseSettingsModal.addEventListener('click', closePlatformSettings);
    }
    if (DOM.platformSettingsModal) {
      DOM.platformSettingsModal.addEventListener('click', (e) => {
        if (e.target === DOM.platformSettingsModal) {
          closePlatformSettings();
        }
      });
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && DOM.platformSettingsModal && DOM.platformSettingsModal.classList.contains('active')) {
        closePlatformSettings();
      }
    });
    if (DOM.modalTabBtnCf) {
      DOM.modalTabBtnCf.addEventListener('click', () => switchSettingsModalTab('cloudflare'));
    }
    if (DOM.modalTabBtnGh) {
      DOM.modalTabBtnGh.addEventListener('click', () => switchSettingsModalTab('github'));
    }
    if (DOM.cfStatusBadge) {
      DOM.cfStatusBadge.addEventListener('click', () => switchTab('tab-deploy', 'cloudflare'));
    }
    if (DOM.gitStatusBadge) {
      DOM.gitStatusBadge.addEventListener('click', () => switchTab('tab-deploy', 'github'));
    }

    // Stepper click handlers
    const stepCards = [DOM.stepCardIngest, DOM.stepCardThemes, DOM.stepCardPosts, DOM.stepCardPlatform, DOM.stepCardDeploy];

    stepCards.forEach((card) => {

      if (card) {

        card.addEventListener('click', () => {

          const target = card.getAttribute('data-target');

          if (target) switchTab(target);

        });

      }

    });



    // Quick Hero Deploy Buttons

    if (DOM.heroCfDeployBtn && DOM.triggerCfDeployBtn) {

      DOM.heroCfDeployBtn.addEventListener('click', () => DOM.triggerCfDeployBtn.click());

    }

    if (DOM.heroGhDeployBtn && DOM.triggerDeployBtn) {

      DOM.heroGhDeployBtn.addEventListener('click', () => DOM.triggerDeployBtn.click());

    }

    if (DOM.triggerBuildGhBtn && DOM.triggerBuildBtn) {

      DOM.triggerBuildGhBtn.addEventListener('click', () => DOM.triggerBuildBtn.click());

    }

  }



  function updateLogoPreview(logoPath, brandName, tagline) {

    const bName = brandName || (DOM.cfgBrandName ? DOM.cfgBrandName.value.trim() : '') || 'Anna Deco';

    const tag = tagline || (DOM.cfgBrandTagline ? DOM.cfgBrandTagline.value.trim() : '') || 'Curated Interior Design & Architectural Aesthetic';



    if (DOM.quickBrandNameDisplay) DOM.quickBrandNameDisplay.textContent = bName;

    if (DOM.previewBrandNameDisplay) DOM.previewBrandNameDisplay.textContent = bName;

    if (DOM.quickTaglineDisplay) DOM.quickTaglineDisplay.textContent = tag;



    const initials = (bName.slice(0, 2) || 'AD').toUpperCase();

    const emblemSvg = `

      <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">

        <circle cx="50" cy="50" r="46" fill="#FAF8F5" stroke="#1C1917" stroke-width="3"/>

        <circle cx="50" cy="50" r="40" fill="none" stroke="#D97706" stroke-width="1.5" stroke-dasharray="3 3"/>

        <path d="M 32 68 L 32 44 C 32 30, 68 30, 68 44 L 68 68 Z" stroke="#1C1917" stroke-width="2.5" fill="none"/>

        <text x="50" y="58" font-family="'Playfair Display', Georgia, serif" font-size="20" font-weight="700" fill="#1C1917" text-anchor="middle">${escapeHtml(initials)}</text>

        <circle cx="50" cy="24" r="3" fill="#D97706"/>

      </svg>`;



    if (logoPath) {

      const logoImgHtml = `<img src="${logoPath}?t=${Date.now()}" alt="${escapeHtml(bName)}" style="max-height: 48px; max-width: 100%; object-fit: contain;">`;

      if (DOM.logoPreviewBox) DOM.logoPreviewBox.innerHTML = logoImgHtml;

      if (DOM.quickLogoPreviewBox) DOM.quickLogoPreviewBox.innerHTML = logoImgHtml;

      if (DOM.previewLogoBox) DOM.previewLogoBox.innerHTML = logoImgHtml;



      const setBadgeActive = (badge) => {

        if (!badge) return;

        badge.textContent = 'Custom Logo Active';

        badge.style.color = '#34D399';

        badge.style.background = 'rgba(16, 185, 129, 0.15)';

        badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';

      };

      setBadgeActive(DOM.logoStatusBadge);

      setBadgeActive(DOM.quickLogoStatusBadge);

      setBadgeActive(DOM.previewLogoStatusBadge);



      const filename = logoPath.split('/').pop();

      if (DOM.logoFilenameText) DOM.logoFilenameText.textContent = `Custom: ${filename}`;

      if (DOM.previewLogoFilename) DOM.previewLogoFilename.textContent = `Custom: ${filename}`;

    } else {

      if (DOM.logoPreviewBox) DOM.logoPreviewBox.innerHTML = emblemSvg;

      if (DOM.quickLogoPreviewBox) DOM.quickLogoPreviewBox.innerHTML = emblemSvg;

      if (DOM.previewLogoBox) DOM.previewLogoBox.innerHTML = emblemSvg;



      const setBadgeDefault = (badge) => {

        if (!badge) return;

        badge.textContent = 'Default Emblem Active';

        badge.style.color = '#F59E0B';

        badge.style.background = 'rgba(245, 158, 11, 0.15)';

        badge.style.borderColor = 'rgba(245, 158, 11, 0.3)';

      };

      setBadgeDefault(DOM.logoStatusBadge);

      setBadgeDefault(DOM.quickLogoStatusBadge);

      setBadgeDefault(DOM.previewLogoStatusBadge);



      if (DOM.logoFilenameText) DOM.logoFilenameText.textContent = 'Default Luxury Vector Emblem';

      if (DOM.previewLogoFilename) DOM.previewLogoFilename.textContent = 'Default Vector SVG Emblem';

    }

  }



  // Load Status and Config

  async function refreshSystem() {

    try {

      const [status, cfg] = await Promise.all([api('/api/status'), api('/api/config')]);

      state.status = status;

      state.config = cfg;



      // Update UI Header & Stats

      DOM.statTotalPosts.textContent = status.total_posts;

      if (DOM.statProjectAssets) {

        DOM.statProjectAssets.textContent = status.local_images_count || 0;

      }

      DOM.statNewPosts.textContent = status.new;

      DOM.statUpdatedPosts.textContent = status.updated;

      DOM.statCustomPosts.textContent = status.custom_edited;

      DOM.statTheme.textContent = status.theme;



      if (status.git_ready) {
        if (DOM.gitStatusText) DOM.gitStatusText.textContent = `${cfg.github?.owner || 'GitHub'}/${cfg.github?.repo || 'Repo'}`;
        if (DOM.gitStatusBadge) DOM.gitStatusBadge.style.color = '#10B981';
      } else {
        if (DOM.gitStatusText) DOM.gitStatusText.textContent = 'GitHub: Not Configured';
        if (DOM.gitStatusBadge) DOM.gitStatusBadge.style.color = '#94A3B8';
      }



      // Cloudflare Header Status Pill

      if (DOM.cfStatusBadge && DOM.cfStatusText) {

        if (status.cloudflare_ready) {

          DOM.cfStatusText.textContent = `Cloudflare: ${cfg.cloudflare?.project_name || 'Ready'}`;

          DOM.cfStatusBadge.classList.add('cf');

          DOM.cfStatusBadge.classList.remove('cf-inactive');

        } else {

          DOM.cfStatusText.textContent = 'Cloudflare: Unconfigured';

          DOM.cfStatusBadge.classList.remove('cf');

          DOM.cfStatusBadge.classList.add('cf-inactive');

        }

      }



      // Populate Cloudflare Settings Inputs

      const cf = cfg.cloudflare || {};

      if (DOM.cfgCfToken) {

        DOM.cfgCfToken.placeholder = cf.token_masked || 'Bearer Token with Workers Edit permissions';

        if (cf.has_token && (!DOM.cfgCfToken.value || DOM.cfgCfToken.value.includes('****'))) {

          DOM.cfgCfToken.value = cf.token_masked || '';

        }

        if (DOM.cfTokenStatusBadge) {

          DOM.cfTokenStatusBadge.textContent = cf.has_token ? '● Token Active' : '○ Missing Token';

          DOM.cfTokenStatusBadge.style.color = cf.has_token ? '#10B981' : '#F59E0B';

        }

      }

      if (DOM.cfgCfAccountId) DOM.cfgCfAccountId.value = cf.account_id || '';
      if (DOM.cfgCfAccountSubdomain) DOM.cfgCfAccountSubdomain.value = cf.account_subdomain || '';
      if (DOM.cfgCfProjectName) DOM.cfgCfProjectName.value = cf.project_name || 'gardenhome';
      if (DOM.cfgCfDeployType) DOM.cfgCfDeployType.value = cf.deployment_type || 'workers_assets';
      if (DOM.cfgCfCustomDomain) DOM.cfgCfCustomDomain.value = cf.custom_domain || '';
      if (DOM.cfgCfCompatibilityDate) DOM.cfgCfCompatibilityDate.value = cf.compatibility_date || '2024-11-01';

      const cfTargetUrl = updateCloudflareLiveUrlPreview();
      if (DOM.cockpitCfWorker) DOM.cockpitCfWorker.textContent = cf.project_name || 'gardenhome';
      if (DOM.cockpitCfSubdomain) DOM.cockpitCfSubdomain.textContent = cf.account_subdomain || '—';



      // Cockpit Meta Updates

      const isCfProj = (typeof currentPlatformMode !== 'undefined' && currentPlatformMode === 'cloudflare') || (state.activePlatform === 'cloudflare') || (!document.getElementById('workspaceCloudflare')?.classList.contains('hidden') && document.getElementById('workspaceCloudflare')?.style.display !== 'none');
      const activeProjToken = isCfProj ? (cfg.cloudflare?.project_name || 'gardenhome') : (cfg.github?.owner || 'annadeco');
      const baseOutDir = (cfg.build?.output_dir && cfg.build.output_dir !== 'distooso') ? cfg.build.output_dir : 'dist';
      if (DOM.cockpitOutputDir) DOM.cockpitOutputDir.textContent = `${baseOutDir}/${activeProjToken}`;

      if (DOM.cockpitTheme) DOM.cockpitTheme.textContent = cfg.build?.theme || 'editorial-warm';

      if (DOM.cockpitGhRepo) DOM.cockpitGhRepo.textContent = cfg.github?.repo || 'homedeco.github.io';
      if (DOM.cockpitGhBranch) DOM.cockpitGhBranch.textContent = cfg.github?.branch || 'main';
      if (DOM.splitCfWorkerName) DOM.splitCfWorkerName.textContent = (cfg.cloudflare && cfg.cloudflare.project_name) ? (cfg.cloudflare.project_name + '.workers.dev') : 'homestylesdeco.workers.dev';
      if (DOM.splitGhRepoName) DOM.splitGhRepoName.textContent = (cfg.github && cfg.github.repo) ? cfg.github.repo : 'annadeco.github.io';

      if (DOM.cockpitGhUrlLink) {

        const ghUrl = cfg.github?.owner && cfg.github?.repo ? `https://${cfg.github.repo}` : '#';

        DOM.cockpitGhUrlLink.textContent = `${ghUrl} ↗`;

        DOM.cockpitGhUrlLink.href = ghUrl;

      }



      // Populate Settings Inputs

      const gh = cfg.github || {};

      DOM.cfgGithubToken.placeholder = gh.token_masked || 'ghp_xxxxxxxxxxxxxxxxxxxx';

      DOM.cfgGithubOwner.value = gh.owner || '';

      DOM.cfgGithubRepo.value = gh.repo || '';

      if (DOM.cfgStep1GithubOwner) DOM.cfgStep1GithubOwner.value = gh.owner || '';
      if (DOM.cfgStep1GithubRepo) DOM.cfgStep1GithubRepo.value = gh.repo || '';

      DOM.cfgGithubBranch.value = gh.branch || 'main';

      DOM.cfgGithubIsOrg.checked = !!gh.is_org;

      DOM.cfgGithubBasePath.value = gh.base_path || '';

      if (DOM.cfgAutoRootOrg) {
        DOM.cfgAutoRootOrg.checked = (gh.repo && gh.repo.endsWith('.github.io')) || (!gh.repo && gh.is_org);
      }
      if (DOM.cfgStep1AutoRootOrg) {
        DOM.cfgStep1AutoRootOrg.checked = (gh.repo && gh.repo.endsWith('.github.io')) || (!gh.repo && gh.is_org);
      }

      updateRootDomainPreview();



      const bld = cfg.build || {};

      const activeTheme = bld.theme || 'nordic-studio';

      const activeRouting = bld.routing_mode || 'single';

      DOM.cfgTheme.value = activeTheme;

      DOM.cfgRoutingMode.value = activeRouting;

      DOM.previewThemeSelect.value = activeTheme;

      DOM.previewRoutingSelect.value = activeRouting;



      // Update active cards in Theme & Routing galleries

      document.querySelectorAll('.theme-card').forEach((card) => {

        if (card.dataset.theme === activeTheme) {

          card.classList.add('active');

        } else {

          card.classList.remove('active');

        }

      });

      document.querySelectorAll('.routing-card').forEach((card) => {

        if (card.dataset.routing === activeRouting) {

          card.classList.add('active');

        } else {

          card.classList.remove('active');

        }

      });

      DOM.cfgOutputDir.value = bld.output_dir || 'dist_github_pages';



      const ing = cfg.ingestion || {};

      DOM.cfgWpApiUrl.value = ing.wp_api_url || 'stylesdays.com';

      DOM.ingestSitemapUrl.value = ing.sitemap_url || 'https://stylesdays.com/sitemap_index.xml';

      DOM.ingestMaxPosts.value = ing.max_posts || 100;

      DOM.ingestDownloadImages.checked = !!ing.download_images;



      // Populate Branding and pSEO settings

      const branding = cfg.branding || status.branding || {};

      if (DOM.cfgBrandName) DOM.cfgBrandName.value = branding.brand_name || 'Anna Deco';

      if (DOM.cfgBrandTagline) DOM.cfgBrandTagline.value = branding.tagline || 'Interior Design & Curated Living';

      if (DOM.cfgAuthorName) DOM.cfgAuthorName.value = branding.author_name || 'Anna Lindqvist';

      if (DOM.cfgAuthorBio) DOM.cfgAuthorBio.value = branding.author_bio || 'Senior Interior Architect & Kinfolk Stylist';

      if (DOM.cfgEnableToc) DOM.cfgEnableToc.checked = branding.enable_toc !== false;

      if (DOM.cfgEnableFaq) DOM.cfgEnableFaq.checked = branding.enable_faq !== false;

      if (DOM.cfgEnableEeat) DOM.cfgEnableEeat.checked = branding.enable_eeat !== false;

      updateLogoPreview(branding.logo_path, branding.brand_name);



      // Populate Preview Options

      DOM.previewThemeSelect.value = bld.theme || 'nordic-studio';

      DOM.previewRoutingSelect.value = bld.routing_mode || 'single';



      await loadGithubAccounts();

      await refreshPosts();

    } catch (err) {

      showToast(`Initialization Error: ${err.message}`, 'error');

    }

  }



  // Load GitHub Organizations List strictly based on token

  async function loadGithubAccounts(customToken = null) {
    const inputToken = (DOM.cfgGithubToken && DOM.cfgGithubToken.value || '').trim();
    const hasSavedToken = !!(state.config && state.config.github && (state.config.github.has_token || state.config.github.token));

    let tokenToSend = '';
    if (customToken && !customToken.includes('****')) {
      tokenToSend = customToken;
    } else if (inputToken && !inputToken.includes('****')) {
      tokenToSend = inputToken;
    }

    // Set loading indicator
    const selects = [DOM.cfgStep1GithubAccount, DOM.selectGithubAccount, DOM.newProjGhOwnerSelect].filter(Boolean);
    selects.forEach(sel => {
      sel.innerHTML = '<option value="">🔄 Detecting organizations from token...</option>';
    });

    if (DOM.tokenStatusBadge) {
      DOM.tokenStatusBadge.textContent = '⏳ Verifying token...';
      DOM.tokenStatusBadge.style.color = '#38BDF8';
    }

    if (!tokenToSend && !hasSavedToken) {
      selects.forEach(sel => {
        sel.innerHTML = '<option value="">⚠️ Enter GitHub Token in Settings to detect accounts</option>';
      });
      if (DOM.tokenStatusBadge) {
        DOM.tokenStatusBadge.textContent = '○ Token Not Configured';
        DOM.tokenStatusBadge.style.color = '#94A3B8';
      }
      if (DOM.step1GithubTokenDetectedBadge) {
        DOM.step1GithubTokenDetectedBadge.textContent = '○ Token Not Configured (Set in Settings)';
        DOM.step1GithubTokenDetectedBadge.style.color = '#F59E0B';
      }
      return;
    }

    try {
      const res = await api('/api/github/orgs', 'POST', { token: tokenToSend });
      if (res.success && res.accounts && res.accounts.length > 0) {
        const currentOwner = (DOM.cfgStep1GithubOwner && DOM.cfgStep1GithubOwner.value || DOM.cfgGithubOwner && DOM.cfgGithubOwner.value || '').trim();

        selects.forEach(sel => {
          sel.innerHTML = '<option value="">-- Choose an Organization or Account --</option>';
          res.accounts.forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.login;
            opt.dataset.isOrg = acc.is_org ? 'true' : 'false';
            const icon = acc.is_org ? '🏢' : '👤';
            opt.textContent = `${icon} ${acc.login} (${acc.type})`;
            if (acc.login === currentOwner) {
              opt.selected = true;
            }
            sel.appendChild(opt);
          });
        });

        if (DOM.tokenStatusBadge) {
          DOM.tokenStatusBadge.textContent = `● Token Connected (${res.accounts.length} accounts detected)`;
          DOM.tokenStatusBadge.style.color = '#10B981';
        }
        if (DOM.step1GithubTokenDetectedBadge) {
          DOM.step1GithubTokenDetectedBadge.textContent = `● ${res.accounts.length} accounts detected from token`;
          DOM.step1GithubTokenDetectedBadge.style.color = '#10B981';
        }

        updateRootDomainPreview();
      } else if (res.token_invalid) {
        selects.forEach(sel => {
          sel.innerHTML = '<option value="">❌ Invalid Token (401 Unauthorized)</option>';
        });
        if (DOM.tokenStatusBadge) {
          DOM.tokenStatusBadge.textContent = '✕ Invalid Token';
          DOM.tokenStatusBadge.style.color = '#EF4444';
        }
        if (DOM.step1GithubTokenDetectedBadge) {
          DOM.step1GithubTokenDetectedBadge.textContent = '✕ Invalid Token in Settings';
          DOM.step1GithubTokenDetectedBadge.style.color = '#EF4444';
        }
      } else {
        selects.forEach(sel => {
          sel.innerHTML = '<option value="">No organizations found on token</option>';
        });
        if (DOM.tokenStatusBadge) {
          DOM.tokenStatusBadge.textContent = '● Connected (0 orgs)';
          DOM.tokenStatusBadge.style.color = '#10B981';
        }
      }
    } catch (err) {
      console.warn('Failed to load GitHub accounts:', err);
      selects.forEach(sel => {
        sel.innerHTML = '<option value="">⚠️ Could not detect accounts</option>';
      });
    }
  }

  
  function populateCategoryFilter() {

    const cats = new Set();

    state.posts.forEach((p) => {

      if (p.category) cats.add(p.category);

    });



    const current = DOM.postCategoryFilter.value;

    DOM.postCategoryFilter.innerHTML = '<option value="">All Categories</option>';

    cats.forEach((c) => {

      const opt = document.createElement('option');

      opt.value = c;

      opt.textContent = c;

      if (c === current) opt.selected = true;

      DOM.postCategoryFilter.appendChild(opt);

    });

  }



  // Populate Preview Select

  function populatePreviewSelect() {

    const current = DOM.previewPostSelect.value || state.selectedPostSlug;

    DOM.previewPostSelect.innerHTML = '';



    // Always provide Front / Homepage Hub as top option so magazine hubs can be previewed immediately

    const hubOpt = document.createElement('option');

    hubOpt.value = '__hub__';

    hubOpt.textContent = '🏛️ Front / Homepage Hub (Model 1 Kinfolk Journal)';

    DOM.previewPostSelect.appendChild(hubOpt);



    // Live Sample Template Post

    const sampleOpt = document.createElement('option');

    sampleOpt.value = '__sample__';

    sampleOpt.textContent = '⭐ Sample Template Post (Scandinavian Room Styling & Checklist)';

    DOM.previewPostSelect.appendChild(sampleOpt);



    state.posts.forEach((p) => {

      const opt = document.createElement('option');

      opt.value = p.slug;

      opt.textContent = `${p.title} (${p.category || 'General'})`;

      if (p.slug === current) {

        opt.selected = true;

      }

      DOM.previewPostSelect.appendChild(opt);

    });



    if (current && current !== '__sample__') {

      DOM.previewPostSelect.value = current;

      state.selectedPostSlug = current;

    } else if (state.posts.length > 0 && !current) {

      DOM.previewPostSelect.value = state.posts[0].slug;

      state.selectedPostSlug = state.posts[0].slug;

    } else {

      DOM.previewPostSelect.value = '__sample__';

      state.selectedPostSlug = '__sample__';

    }



    if (state.selectedPostSlug === '__sample__') {

      DOM.previewLiveTitle.value = 'Modern Scandinavian Living Room Design: 15 Warm Minimalist Ideas';

      if (DOM.previewLiveExcerpt) DOM.previewLiveExcerpt.value = 'Transform your main living space with organic textures, functional hidden storage, and warm lighting layers designed for everyday comfort.';

    } else if (state.selectedPostSlug) {

      const post = state.posts.find((p) => p.slug === state.selectedPostSlug);

      if (post) {

        DOM.previewLiveTitle.value = post.title || '';

        if (DOM.previewLiveExcerpt) DOM.previewLiveExcerpt.value = post.excerpt || '';

      }

    }

  }



  // Refresh Posts Catalog
  async function refreshPosts() {
    try {
      const q = DOM.postSearchInput ? DOM.postSearchInput.value.trim() : '';
      const cat = DOM.postCategoryFilter ? DOM.postCategoryFilter.value : '';
      const statusFilter = DOM.postStatusFilter ? DOM.postStatusFilter.value : '';
      const customOnly = statusFilter === 'CUSTOM';
      const res = await api(`/api/posts?q=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}&custom_only=${customOnly}`);
      state.posts = res.posts || [];
      renderPostsTable();
      populateCategoryFilter();
      populatePreviewSelect();
    } catch (err) {
      showToast(`Error fetching posts: ${err.message}`, 'error');
    }
  }

  // Render Posts Catalog Table

  function renderPostsTable() {

    DOM.postsCatalogBody.innerHTML = '';

    if (state.posts.length === 0) {

      DOM.postsCatalogBody.innerHTML = `

        <tr>

          <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-secondary);">

            No matching posts found. Ingest content from the "Ingestion & Manifest" tab.

          </td>

        </tr>`;

      return;

    }



    state.posts.forEach((post) => {

      const tr = document.createElement('tr');

      const badgeClass = post.custom_edited ? 'badge-custom' : 'badge-synced';

      const badgeText = post.custom_edited ? 'CUSTOM' : 'SYNCED';

      const thumb = post.local_image_path || `/assets/images/${post.slug}.svg`;



      tr.innerHTML = `

        <td><span class="badge ${badgeClass}">${badgeText}</span></td>

        <td>

          <img src="${thumb}" alt="" style="width: 44px; height: 30px; object-fit: cover; border-radius: 4px; background: #334155;" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'44\\' height=\\'30\\'><rect width=\\'44\\' height=\\'30\\' fill=\\'%23334155\\'/></svg>'">

        </td>

        <td>

          <div style="font-weight: 600; color: var(--text-primary);">${escapeHtml(post.title)}</div>

          <div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted);">${escapeHtml(post.slug)}</div>

        </td>

        <td><span class="badge" style="background: rgba(255,255,255,0.08);">${escapeHtml(post.category || 'General')}</span></td>

        <td style="font-size: 0.75rem; color: var(--text-secondary);">${(post.modified || post.date || '').slice(0, 10)}</td>

        <td>${post.custom_edited ? '✅ Yes' : '—'}</td>

        <td>

          <div style="display: flex; gap: 0.35rem;">

            <button class="btn btn-secondary btn-sm edit-btn" data-slug="${post.slug}">✏️ Edit</button>

            <button class="btn btn-secondary btn-sm preview-btn" data-slug="${post.slug}">👁️ Preview</button>

          </div>

        </td>

      `;



      tr.querySelector('.edit-btn').addEventListener('click', () => openEditModal(post.slug));

      tr.querySelector('.preview-btn').addEventListener('click', () => {

        state.selectedPostSlug = post.slug;

        DOM.previewPostSelect.value = post.slug;

        const targetTab = document.querySelector('[data-tab="tab-preview"]');

        if (targetTab) targetTab.click();

      });



      DOM.postsCatalogBody.appendChild(tr);

    });

  }



  // Open Edit Modal

  async function openEditModal(slug) {

    try {

      const post = await api(`/api/posts/${slug}`);

      DOM.editPostSlug.value = post.slug;

      DOM.modalPostSlugTitle.textContent = `Edit Post: ${post.slug}`;

      DOM.editPostTitle.value = post.title || '';

      if (DOM.editPostExcerpt) DOM.editPostExcerpt.value = post.excerpt || '';

      DOM.editPostCategory.value = post.category || '';

      DOM.editPostParentSlug.value = post.parent_slug || '';



      // Populate Takeaways
      if (DOM.editTakeawaysContainer) {
        DOM.editTakeawaysContainer.innerHTML = '';
        (post.takeaways || []).forEach((t) => addTakeawayInput(t));
      }

      // Populate Checklist
      if (DOM.editChecklistContainer) {
        DOM.editChecklistContainer.innerHTML = '';
        (post.checklist || []).forEach((c) => addChecklistInput(c.text || c));
      }



      DOM.postEditModal.classList.add('active');

    } catch (err) {

      showToast(`Failed loading post: ${err.message}`, 'error');

    }

  }



  function addTakeawayInput(text = '') {

    const row = document.createElement('div');

    row.style.display = 'flex';

    row.style.gap = '0.5rem';

    row.innerHTML = `

      <input type="text" class="form-control takeaway-input" value="${escapeHtml(text)}" placeholder="Enter takeaway tip...">

      <button type="button" class="btn btn-secondary btn-sm delete-btn" style="color: #EF4444;">✕</button>

    `;

    row.querySelector('.delete-btn').addEventListener('click', () => row.remove());

    if (DOM.editTakeawaysContainer) DOM.editTakeawaysContainer.appendChild(row);

  }



  function addChecklistInput(text = '') {

    const row = document.createElement('div');

    row.style.display = 'flex';

    row.style.gap = '0.5rem';

    row.innerHTML = `

      <input type="text" class="form-control checklist-input" value="${escapeHtml(text)}" placeholder="Enter prep checklist step...">

      <button type="button" class="btn btn-secondary btn-sm delete-btn" style="color: #EF4444;">✕</button>

    `;

    row.querySelector('.delete-btn').addEventListener('click', () => row.remove());

    if (DOM.editChecklistContainer) DOM.editChecklistContainer.appendChild(row);

  }



  // Save Modal Post

  async function handlePostSave(e) {

    e.preventDefault();

    const slug = DOM.editPostSlug.value;

    const title = DOM.editPostTitle.value.trim();

    const excerpt = DOM.editPostExcerpt ? DOM.editPostExcerpt.value.trim() : '';

    const category = DOM.editPostCategory.value.trim();

    const parent_slug = DOM.editPostParentSlug.value.trim();



    const takeaways = [];

    document.querySelectorAll('.takeaway-input').forEach((inp) => {

      if (inp.value.trim()) takeaways.push(inp.value.trim());

    });



    const checklist = [];

    document.querySelectorAll('.checklist-input').forEach((inp, idx) => {

      if (inp.value.trim()) {

        checklist.push({ id: `${slug}-step-${idx + 1}`, text: inp.value.trim() });

      }

    });



    try {

      await api(`/api/posts/${slug}`, 'PUT', {

        title,

        excerpt,

        category,

        parent_slug,

        takeaways,

        checklist,

      });



      DOM.postEditModal.classList.remove('active');

      showToast(`Saved changes for '${slug}' (marked custom edited)`, 'success');

      await refreshSystem();

    } catch (err) {

      showToast(`Error saving post: ${err.message}`, 'error');

    }

  }



  // ─── Model Switcher: 1-click preview with theme-specific demo content ────────

  function initModelSwitcher() {

    const modelBtns = document.querySelectorAll('.model-preview-btn');

    const THEME_ACCENT = {

      'editorial-warm': '#E7E2DA',

      'nordic-studio':  '#0F766E',

      'pinterest-mag':  '#BE123C',

    };

    const THEME_DEMOS = {

      'editorial-warm': {

        slug: '15-home-bedroom-refresh-ideas-transform-your-oasis',

        title: '15 Bedroom Refresh Ideas: Transform Your Oasis with Linen & Warmth',

        excerpt: 'A warm, editorial-styled bedroom sanctuary using Belgian linen bedding, bouclé accents, and Playfair serif typography — sourced exclusively from the Kinfolk slow-living aesthetic.',

        local_image_path: '/assets/images/15-home-bedroom-refresh-ideas-transform-your-oasis.webp',

        category: 'Bedroom Refresh',

        category_slug: 'bedroom-refresh',

        parent_slug: 'bedroom-ideas',

        date: '2026-10-15',

        takeaways: [

          'Belgian Linen Bedding: Choose natural flax weave in fog or oat colourways for a lived-in warmth.',

          'Warm Amber Lighting: Install 2700K Edison pendants at 3 varying heights to eliminate cold dark corners.',

          'Editor Sourcing: Source bouclé throws from ethical Merino wool producers for lasting tactile comfort.',

        ],

        checklist: [

          { id: 'step-1', text: 'Wash and pre-shrink all linen bedding before making up the bed' },

          { id: 'step-2', text: 'Layer textures: linen duvet + woven throw + embroidered cushions' },

          { id: 'step-3', text: 'Install warm amber bulb pendants with dimmable switch' },

          { id: 'step-4', text: 'Add live dried botanicals (pampas, lunaria) for editorial styling' },

        ],

      },

      'nordic-studio': {

        slug: '20-modern-bedroom-ideas-transform-your-space-with-style',

        title: '20 Modern Bedroom Ideas: Transform Your Space with Architectural Style',

        excerpt: 'An asymmetric 2-column architectural studio layout featuring technical spec drawers with room dimensions, 2700K lighting specs, White Oak herringbone flooring plans, and matte black hardware finishes.',

        local_image_path: '/assets/images/20-modern-bedroom-ideas-transform-your-space-with-style.webp',

        category: 'Modern Architecture',

        category_slug: 'modern-architecture',

        parent_slug: 'bedroom-ideas',

        date: '2026-10-20',

        takeaways: [

          'Room Dimensions First: Always start with a measured floor plan — 14ft × 16ft is the ideal studio bedroom.',

          'Lighting Specification: 2700K warm neutral kelvin ceiling and task lights create architectural depth.',

          'White Oak Herringbone: Parquet flooring in wide plank or herringbone adds tactile geometric character.',

        ],

        checklist: [

          { id: 'step-1', text: 'Draft a scaled floor plan at 14ft x 16ft with traffic flow paths mapped' },

          { id: 'step-2', text: 'Source White Oak herringbone flooring samples and compare plank widths' },

          { id: 'step-3', text: 'Install 2700K warm neutral ceiling lights + bedside task lighting' },

          { id: 'step-4', text: 'Select matte black hardware for wardrobe, drawers, and door levers' },

        ],

      },

      'pinterest-mag': {

        slug: '16-coastal-bedroom-decor-essentials-transform-your-space',

        title: '16 Coastal Bedroom Decor Essentials: Transform Your Beach House Space',

        excerpt: 'A high-fashion visual pin discovery magazine layout with floating 📌 Save to Pinterest badge, 2-column moodboard pin cards, 98% viral save score bar, and ruby-red editorial accents for coastal beach house decor.',

        local_image_path: '/assets/images/16-coastal-bedroom-decor-essentials-transform-your-space.webp',

        category: 'Coastal Decor',

        category_slug: 'coastal-decor',

        parent_slug: 'bedroom-ideas',

        date: '2026-10-16',

        takeaways: [

          'Coastal Palette: Sandy neutrals, seafoam whites, and driftwood greys create instant beach house atmosphere.',

          'Natural Fibre Textiles: Jute rugs, linen throws, and rattan furniture bring organic coastal warmth indoors.',

          'Pinterest-Worthy Styling: Vertical stripes, oversized mirrors, and layered cushion arrangements drive 98% save rates.',

        ],

        checklist: [

          { id: 'step-1', text: 'Choose a coastal neutral palette: Sandy, Seafoam, Driftwood, and Coral accent' },

          { id: 'step-2', text: 'Source jute or seagrass rug as the room anchor piece' },

          { id: 'step-3', text: 'Add 3 layers of cushions in varying textures: linen, velvet, embroidered' },

          { id: 'step-4', text: 'Style a decorative shelf with shells, coral pieces, and whitewashed driftwood frames' },

        ],

      },

    };



    modelBtns.forEach((btn) => {

      btn.addEventListener('click', async () => {

        const theme = btn.getAttribute('data-theme');

        if (!theme) return;



        // Update visual active state on model buttons

        modelBtns.forEach((b) => {

          b.style.boxShadow = '';

          b.style.borderWidth = '2px';

        });

        const accentMap = { 'editorial-warm': '#E60023', 'nordic-studio': '#8C6D53', 'pinterest-mag': '#BE123C' };

        btn.style.boxShadow = `0 0 0 2px ${accentMap[theme] || '#666'}`;

        btn.style.borderColor = accentMap[theme] || '#666';



        // Set the theme dropdown

        if (DOM.previewThemeSelect) DOM.previewThemeSelect.value = theme;



        // Check if button requested Homepage Hub preview
        const viewMode = btn.getAttribute('data-view') || 'post';
        if (viewMode === 'hub') {
          if (DOM.previewPostSelect) DOM.previewPostSelect.value = '__hub__';
          state.selectedPostSlug = '__hub__';
          try {
            const res = await api('/api/preview', 'POST', {
              theme,
              routing_mode: DOM.previewRoutingSelect ? DOM.previewRoutingSelect.value : 'single',
              view_mode: 'hub',
              slug: '__hub__',
            });
            if (res.html && DOM.previewIframe) {
              DOM.previewIframe.srcdoc = res.html;
            }
          } catch (err) {
            showToast(`Model hub preview failed: ${err.message}`, 'error');
          }
          return;
        }

        // Get demo data for this theme

        const demo = THEME_DEMOS[theme];

        if (!demo) return;



        // Update form fields with demo content

        if (DOM.previewLiveTitle) DOM.previewLiveTitle.value = demo.title;

        if (DOM.previewLiveExcerpt) DOM.previewLiveExcerpt.value = demo.excerpt;



        // Select the sample template option

        if (DOM.previewPostSelect) DOM.previewPostSelect.value = '__sample__';

        state.selectedPostSlug = '__sample__';



        // Render preview immediately with full demo post

        try {

          const payload = {

            theme,

            routing_mode: DOM.previewRoutingSelect ? DOM.previewRoutingSelect.value : 'single',

            post: {

              slug: demo.slug,

              title: demo.title,

              excerpt: demo.excerpt,

              category: demo.category,

              category_slug: demo.category_slug,

              parent_slug: demo.parent_slug,

              date: demo.date,

              local_image_path: demo.local_image_path,

              takeaways: demo.takeaways,

              checklist: demo.checklist,

            },

          };

          const res = await api('/api/preview', 'POST', payload);

          if (res.html && DOM.previewIframe) {

            DOM.previewIframe.srcdoc = res.html;

          }

        } catch (err) {

          showToast(`Model preview failed: ${err.message}`, 'error');

        }

      });

    });

  }



  // Live Preview Engine

  async function triggerPreview() {

    const slug = DOM.previewPostSelect.value || state.selectedPostSlug || '__sample__';



    const theme = DOM.previewThemeSelect.value || DOM.cfgTheme?.value || 'nordic-studio';

    const routingMode = DOM.previewRoutingSelect.value || DOM.cfgRoutingMode?.value || 'single';

    const overrideTitle = DOM.previewLiveTitle.value.trim();

    const overrideExcerpt = DOM.previewLiveExcerpt ? DOM.previewLiveExcerpt.value.trim() : '';



    try {

      const isHub = (slug === '__hub__');
      const payload = {

        theme,

        routing_mode: routingMode,

        view_mode: isHub ? 'hub' : 'post',

        slug: slug,

      };



      if (slug === '__sample__') {

        payload.post = {

          slug: 'modern-room-styling-guide',

          title: overrideTitle || 'Modern Scandinavian Living Room Design: 15 Warm Minimalist Ideas',

          excerpt: overrideExcerpt || 'Transform your main living space with organic textures, functional hidden storage, and warm lighting layers designed for everyday comfort.',

          category: 'Living Room Styling',

          category_slug: 'living-room',

          parent_slug: 'home-organization',

          date: '2026-11-02',

          takeaways: [

            'Balanced Room Proportions: Anchor your layout with clean-lined low profile seating.',

            'Layered Textures: Blend natural oak, boucle, and linen for Scandinavian warmth.',

            'Intentional Lighting: Use 3 light sources at varying heights to eliminate dark corners.',

          ],

          checklist: [

            { id: 'step-1', text: 'Measure room footprint and map primary natural light windows' },

            { id: 'step-2', text: 'Select foundational neutral furniture pieces (boucle, warm oak)' },

            { id: 'step-3', text: 'Install warm-toned 2700K ambient and task lighting fixtures' },

          ],

        };

      } else {

        payload.slug = slug;

        if (overrideTitle || overrideExcerpt) {

          const post = state.posts.find((p) => p.slug === slug);

          if (post) {

            payload.post = {

              ...post,

              title: overrideTitle || post.title,

              excerpt: overrideExcerpt || post.excerpt,

            };

          }

        }

      }



      const res = await api('/api/preview', 'POST', payload);

      if (res.html) {

        DOM.previewIframe.srcdoc = res.html;

      }

    } catch (err) {

      showToast(`Preview render failed: ${err.message}`, 'error');

    }

  }



    function updateRootDomainPreview() {
    const owner = (DOM.cfgStep1GithubOwner && DOM.cfgStep1GithubOwner.value || DOM.cfgGithubOwner && DOM.cfgGithubOwner.value || '').trim();
    const isAuto = (DOM.cfgStep1AutoRootOrg ? DOM.cfgStep1AutoRootOrg.checked : (DOM.cfgAutoRootOrg ? DOM.cfgAutoRootOrg.checked : false));

    if (isAuto && owner) {
      if (DOM.cfgStep1GithubRepo) DOM.cfgStep1GithubRepo.value = `${owner}.github.io`;
      if (DOM.cfgGithubRepo) DOM.cfgGithubRepo.value = `${owner}.github.io`;
      if (DOM.cfgGithubIsOrg) DOM.cfgGithubIsOrg.checked = true;
    }

    const repo = (DOM.cfgStep1GithubRepo && DOM.cfgStep1GithubRepo.value || DOM.cfgGithubRepo && DOM.cfgGithubRepo.value || '').trim();
    let previewHtml = '';
    if (repo.endsWith('.github.io') || (!repo && owner)) {
      const domain = repo.endsWith('.github.io') ? repo : `${owner}.github.io`;
      previewHtml = `Target: <a href="https://${domain}" target="_blank" rel="noopener" style="color:#34D399;font-weight:bold;text-decoration:none;">https://${domain}/</a>`;
    } else if (owner && repo) {
      previewHtml = `Target: <a href="https://${owner}.github.io/${repo}/" target="_blank" rel="noopener" style="color:#38BDF8;font-weight:bold;text-decoration:none;">https://${owner}.github.io/${repo}/</a>`;
    } else {
      previewHtml = 'Target: https://&lt;org&gt;.github.io/';
    }

    if (DOM.rootDomainPreview) DOM.rootDomainPreview.innerHTML = previewHtml;
    if (DOM.step1RootDomainPreview) DOM.step1RootDomainPreview.innerHTML = previewHtml;
  }



  // Event Listeners Setup

  function initListeners() {

    // Subtab Switching (Cloudflare, GitHub Pages, Build Settings)

    if (DOM.subtabBtns) {

      DOM.subtabBtns.forEach((btn) => {

        btn.addEventListener('click', () => {

          const target = btn.getAttribute('data-subtab');

          DOM.subtabBtns.forEach((b) => b.classList.remove('active'));

          DOM.subtabPanes.forEach((p) => p.classList.remove('active'));



          btn.classList.add('active');

          const targetPane = document.getElementById(target);

          if (targetPane) targetPane.classList.add('active');

        });

      });

    }



    // Token Visibility Eye Toggles

    if (DOM.toggleCfTokenEye && DOM.cfgCfToken) {

      DOM.toggleCfTokenEye.addEventListener('click', () => {

        const isPass = DOM.cfgCfToken.type === 'password';

        DOM.cfgCfToken.type = isPass ? 'text' : 'password';

        DOM.toggleCfTokenEye.textContent = isPass ? '🔒' : '👁️';

      });

    }



    if (DOM.toggleGhTokenEye && DOM.cfgGithubToken) {

      DOM.toggleGhTokenEye.addEventListener('click', () => {

        const isPass = DOM.cfgGithubToken.type === 'password';

        DOM.cfgGithubToken.type = isPass ? 'text' : 'password';

        DOM.toggleGhTokenEye.textContent = isPass ? '🔒' : '👁️';

      });

    }



    // Cloudflare Settings Form Submit

    if (DOM.cloudflareSettingsForm) {

      DOM.cloudflareSettingsForm.addEventListener('submit', async (e) => {

        e.preventDefault();

        try {

          const payload = {

            cloudflare: {

              token: DOM.cfgCfToken.value.trim(),

              api_token: DOM.cfgCfToken.value.trim(),

              account_id: DOM.cfgCfAccountId.value.trim(),

              account_subdomain: (DOM.cfgCfAccountSubdomain && DOM.cfgCfAccountSubdomain.value.trim()) || '',

              project_name: DOM.cfgCfProjectName.value.trim(),

              deployment_type: DOM.cfgCfDeployType.value,

              custom_domain: DOM.cfgCfCustomDomain.value.trim(),

              compatibility_date: DOM.cfgCfCompatibilityDate.value.trim(),

            },

          };

          await api('/api/config', 'POST', payload);

          showToast('Cloudflare configuration saved successfully.', 'success');

          if (DOM.cfStatusFeedback) {

            DOM.cfStatusFeedback.style.display = 'block';

            DOM.cfStatusFeedback.style.background = 'rgba(16, 185, 129, 0.18)';

            DOM.cfStatusFeedback.style.color = '#34D399';

            DOM.cfStatusFeedback.innerHTML = '💾 <strong>Saved!</strong> Cloudflare settings saved and configuration updated on disk.';

          }

          if (DOM.cfStatusBadge && DOM.cfStatusText) {

            const proj = DOM.cfgCfProjectName.value.trim() || 'Ready';

            DOM.cfStatusText.textContent = `Cloudflare: ${proj}`;

            DOM.cfStatusBadge.classList.add('cf');

            DOM.cfStatusBadge.classList.remove('cf-inactive');

          }

          await refreshSystem();

        } catch (err) {

          showToast(`Cloudflare save error: ${err.message}`, 'error');

          if (DOM.cfStatusFeedback) {

            DOM.cfStatusFeedback.style.display = 'block';

            DOM.cfStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';

            DOM.cfStatusFeedback.style.color = '#FCA5A5';

            DOM.cfStatusFeedback.innerHTML = `❌ <strong>Save Error:</strong> ${escapeHtml(err.message)}`;

          }

        }

      });

    }



    // Cloudflare Token Verification Action

    if (DOM.btnVerifyCfToken) {

      DOM.btnVerifyCfToken.addEventListener('click', async () => {

        let token = (DOM.cfgCfToken && DOM.cfgCfToken.value || '').trim();

        if (token.includes('****')) {

          token = ''; // let server use the saved config token

        }

        const accountId = (DOM.cfgCfAccountId && DOM.cfgCfAccountId.value || '').trim();

        DOM.cfStatusFeedback.style.display = 'block';

        DOM.cfStatusFeedback.style.background = 'rgba(59, 130, 246, 0.15)';

        DOM.cfStatusFeedback.style.color = '#93C5FD';

        DOM.cfStatusFeedback.innerHTML = '⏳ Verifying Cloudflare credentials against Cloudflare API...';



        try {

          const res = await api('/api/cloudflare/verify', 'POST', { token, account_id: accountId });

          if (res.success && res.verified) {

            DOM.cfStatusFeedback.style.background = 'rgba(16, 185, 129, 0.18)';

            DOM.cfStatusFeedback.style.color = '#34D399';

            const subInfo = res.subdomain ? ` (Subdomain: <code>${escapeHtml(res.subdomain)}</code>)` : '';
            DOM.cfStatusFeedback.innerHTML = `✅ <strong>Verified!</strong> Cloudflare Token is active for Account <code>${escapeHtml(res.account_id || accountId || 'Auto')}</code>${subInfo}.`;

            if (res.subdomain && DOM.cfgCfAccountSubdomain) {
              DOM.cfgCfAccountSubdomain.value = res.subdomain;
            }
            updateCloudflareLiveUrlPreview();

            if (DOM.cfTokenStatusBadge) {

              DOM.cfTokenStatusBadge.textContent = '● Verified Active';

              DOM.cfTokenStatusBadge.style.color = '#10B981';

            }

            if (DOM.cfStatusBadge && DOM.cfStatusText) {

              const proj = (DOM.cfgCfProjectName && DOM.cfgCfProjectName.value.trim()) || 'Ready';

              DOM.cfStatusText.textContent = `Cloudflare: ${proj}`;

              DOM.cfStatusBadge.classList.add('cf');

              DOM.cfStatusBadge.classList.remove('cf-inactive');

            }

            showToast('Cloudflare credentials verified successfully!', 'success');

          } else {

            DOM.cfStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';

            DOM.cfStatusFeedback.style.color = '#FCA5A5';

            DOM.cfStatusFeedback.innerHTML = `❌ Verification failed: ${escapeHtml(res.error || 'Invalid credentials')}`;

            if (DOM.cfTokenStatusBadge) {

              DOM.cfTokenStatusBadge.textContent = '✕ Invalid Token';

              DOM.cfTokenStatusBadge.style.color = '#EF4444';

            }

            showToast(res.error || 'Verification failed', 'error');

          }

        } catch (err) {

          DOM.cfStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';

          DOM.cfStatusFeedback.style.color = '#FCA5A5';

          DOM.cfStatusFeedback.innerHTML = `❌ Error: ${escapeHtml(err.message)}`;

          showToast(`Verification error: ${err.message}`, 'error');

        }

      });

    }



    // Dynamic Cloudflare Live URL Preview
    [DOM.cfgCfProjectName, DOM.cfgCfAccountSubdomain, DOM.cfgCfCustomDomain].forEach((inputEl) => {
      if (inputEl) {
        inputEl.addEventListener('input', updateCloudflareLiveUrlPreview);
      }
    });
    if (DOM.cfgCfDeployType) {
      DOM.cfgCfDeployType.addEventListener('change', updateCloudflareLiveUrlPreview);
    }

    // Auto-save Project Name and Custom Domain from Ingest Step
    const saveIngestProjectConfig = async () => {
      try {
        const proj = (DOM.cfgCfProjectName && DOM.cfgCfProjectName.value.trim()) || 'gardenhome';
        const custom = (DOM.cfgCfCustomDomain && DOM.cfgCfCustomDomain.value.trim()) || '';
        await api('/api/config', 'POST', {
          cloudflare: {
            project_name: proj,
            custom_domain: custom,
          },
        });
        updateCloudflareLiveUrlPreview();
      } catch (err) {
        console.warn('Auto-save of project name or custom domain failed:', err);
      }
    };
    if (DOM.cfgCfProjectName) DOM.cfgCfProjectName.addEventListener('change', saveIngestProjectConfig);
    if (DOM.cfgCfCustomDomain) DOM.cfgCfCustomDomain.addEventListener('change', saveIngestProjectConfig);



    // Dynamic Token Auto-Detection Listener

    let tokenTimer = null;

    if (DOM.cfgGithubToken) {

      DOM.cfgGithubToken.addEventListener('input', () => {

        clearTimeout(tokenTimer);

        const val = DOM.cfgGithubToken.value.trim();

        if (!val || val.includes('****')) {

          loadGithubAccounts(null);

          return;

        }

        if (val.length >= 25) {

          tokenTimer = setTimeout(() => {

            loadGithubAccounts(val);

          }, 600);

        }

      });



      DOM.cfgGithubToken.addEventListener('paste', () => {

        setTimeout(() => {

          const val = DOM.cfgGithubToken.value.trim();

          if (val && !val.includes('****')) {

            loadGithubAccounts(val);

          }

        }, 150);

      });

    }



    if (DOM.cfgGithubOwner) {

      DOM.cfgGithubOwner.addEventListener('input', updateRootDomainPreview);

    }

    if (DOM.cfgAutoRootOrg) {

      DOM.cfgAutoRootOrg.addEventListener('change', updateRootDomainPreview);

    }

    if (DOM.cfgGithubRepo) {

      DOM.cfgGithubRepo.addEventListener('input', () => {

        if (DOM.cfgAutoRootOrg && !DOM.cfgGithubRepo.value.endsWith('.github.io')) {

          DOM.cfgAutoRootOrg.checked = false;

        }

        updateRootDomainPreview();

      });

    }



    // =========================================================================
    // STEP 1 GITHUB TARGET ROUTING & DETECTED ACCOUNT LISTENERS
    // =========================================================================
    if (DOM.cfgStep1GithubAccount) {
      DOM.cfgStep1GithubAccount.addEventListener('change', async () => {
        const val = DOM.cfgStep1GithubAccount.value;
        if (!val) return;
        const opt = DOM.cfgStep1GithubAccount.selectedOptions[0];
        const isOrg = opt ? opt.dataset.isOrg === 'true' : false;

        if (DOM.cfgStep1GithubOwner) DOM.cfgStep1GithubOwner.value = val;
        if (DOM.cfgGithubOwner) DOM.cfgGithubOwner.value = val;
        if (DOM.cfgGithubIsOrg) DOM.cfgGithubIsOrg.checked = isOrg;

        if (DOM.cfgStep1AutoRootOrg && DOM.cfgStep1AutoRootOrg.checked) {
          if (DOM.cfgStep1GithubRepo) DOM.cfgStep1GithubRepo.value = `${val}.github.io`;
          if (DOM.cfgGithubRepo) DOM.cfgGithubRepo.value = `${val}.github.io`;
        }
        updateRootDomainPreview();
        try {
          await api('/api/config', 'POST', {
            github: {
              owner: val,
              repo: DOM.cfgStep1GithubRepo ? DOM.cfgStep1GithubRepo.value.trim() : `${val}.github.io`,
              is_org: isOrg
            }
          });
          showToast(`GitHub Organization set to '${val}'`, 'info');
        } catch (e) {
          console.warn('Auto-save of GitHub owner failed:', e);
        }
      });
    }

    if (DOM.btnRefreshStep1Orgs) {
      DOM.btnRefreshStep1Orgs.addEventListener('click', async () => {
        if (DOM.cfgStep1GithubAccount) {
          DOM.cfgStep1GithubAccount.innerHTML = '<option value="">🔄 Refreshing organizations...</option>';
        }
        await loadGithubAccounts();
        showToast('GitHub accounts refreshed from API.', 'info');
      });
    }

    if (DOM.cfgStep1AutoRootOrg) {
      DOM.cfgStep1AutoRootOrg.addEventListener('change', () => {
        updateRootDomainPreview();
        if (DOM.cfgStep1GithubRepo) {
          api('/api/config', 'POST', { github: { repo: DOM.cfgStep1GithubRepo.value.trim() } }).catch(() => {});
        }
      });
    }

    if (DOM.btnStep1CheckOrg) {
      DOM.btnStep1CheckOrg.addEventListener('click', async () => {
        const orgName = (DOM.cfgStep1GithubOwner ? DOM.cfgStep1GithubOwner.value : '').trim();
        let token = (DOM.cfgGithubToken ? DOM.cfgGithubToken.value : '').trim();
        if (token.includes('****')) token = '';
        if (!orgName) {
          showToast('Please enter or select an Organization first.', 'error');
          if (DOM.cfgStep1GithubOwner) DOM.cfgStep1GithubOwner.focus();
          return;
        }
        DOM.btnStep1CheckOrg.disabled = true;
        DOM.btnStep1CheckOrg.innerHTML = '<span>⏳ Querying GitHub API...</span>';
        if (DOM.step1OrgStatusFeedback) {
          DOM.step1OrgStatusFeedback.style.display = 'block';
          DOM.step1OrgStatusFeedback.style.background = 'rgba(59, 130, 246, 0.15)';
          DOM.step1OrgStatusFeedback.style.color = '#93C5FD';
          DOM.step1OrgStatusFeedback.innerHTML = `Checking status of organization <strong>${orgName}</strong> on GitHub...`;
        }
        try {
          const res = await api('/api/github/check-org', 'POST', { org: orgName, token: token });
          if (res.exists) {
            if (DOM.step1OrgStatusFeedback) {
              DOM.step1OrgStatusFeedback.style.background = 'rgba(16, 185, 129, 0.18)';
              DOM.step1OrgStatusFeedback.style.color = '#34D399';
              DOM.step1OrgStatusFeedback.innerHTML = `✅ <strong>${res.message}</strong><br><small>Plan: ${res.details?.plan || 'Free'} | Verified repository container ready.</small>`;
            }
            if (DOM.cfgGithubIsOrg) DOM.cfgGithubIsOrg.checked = true;
            showToast(`Organization '${orgName}' is ready!`, 'success');
          } else {
            if (DOM.step1OrgStatusFeedback) {
              DOM.step1OrgStatusFeedback.style.background = 'rgba(245, 158, 11, 0.18)';
              DOM.step1OrgStatusFeedback.style.color = '#FCD34D';
              DOM.step1OrgStatusFeedback.innerHTML = `⚠️ <strong>${res.message}</strong><br><small style="color:#E2E8F0;">${res.api_limitation || ''}</small>`;
            }
            if (DOM.linkStep1OpenGithubOrg) {
              DOM.linkStep1OpenGithubOrg.style.display = 'inline-flex';
              DOM.linkStep1OpenGithubOrg.href = res.create_web_url || 'https://github.com/account/organizations/new?plan=free';
            }
            showToast(`Organization '${orgName}' needs to be created on GitHub.`, 'warning');
          }
        } catch (err) {
          if (DOM.step1OrgStatusFeedback) {
            DOM.step1OrgStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';
            DOM.step1OrgStatusFeedback.style.color = '#FCA5A5';
            DOM.step1OrgStatusFeedback.innerHTML = `❌ Error: ${err.message}`;
          }
        } finally {
          DOM.btnStep1CheckOrg.disabled = false;
          DOM.btnStep1CheckOrg.innerHTML = '<span>🏢 Verify Org</span>';
        }
      });
    }

    if (DOM.btnStep1CreateRepo) {
      DOM.btnStep1CreateRepo.addEventListener('click', async () => {
        const owner = (DOM.cfgStep1GithubOwner ? DOM.cfgStep1GithubOwner.value : '').trim();
        const repo = (DOM.cfgStep1GithubRepo ? DOM.cfgStep1GithubRepo.value : '').trim();
        let token = (DOM.cfgGithubToken ? DOM.cfgGithubToken.value : '').trim();
        if (token.includes('****')) token = '';
        if (!owner || !repo) {
          showToast('Please enter Organization and Repository Name first.', 'error');
          return;
        }
        DOM.btnStep1CreateRepo.disabled = true;
        DOM.btnStep1CreateRepo.innerHTML = '<span>⏳ Creating Repo on GitHub...</span>';
        if (DOM.step1OrgStatusFeedback) {
          DOM.step1OrgStatusFeedback.style.display = 'block';
          DOM.step1OrgStatusFeedback.style.background = 'rgba(59, 130, 246, 0.15)';
          DOM.step1OrgStatusFeedback.style.color = '#93C5FD';
          DOM.step1OrgStatusFeedback.innerHTML = `Creating repository <strong>${owner}/${repo}</strong> on GitHub...`;
        }
        try {
          const res = await api('/api/github/create-repo', 'POST', {
            owner,
            repo,
            is_org: true,
            token: token
          });
          if (res.success) {
            if (DOM.step1OrgStatusFeedback) {
              DOM.step1OrgStatusFeedback.style.background = 'rgba(16, 185, 129, 0.18)';
              DOM.step1OrgStatusFeedback.style.color = '#34D399';
              DOM.step1OrgStatusFeedback.innerHTML = `✅ <strong>Repository '${owner}/${repo}' Ready!</strong><br><small><a href="${res.repo_url}" target="_blank" style="color:#60A5FA;">↗ View on GitHub</a> | Pages: <a href="${res.pages_url}" target="_blank" style="color:#34D399;">${res.pages_url}</a></small>`;
            }
            showToast(`Repository '${owner}/${repo}' configured!`, 'success');
          } else {
            if (DOM.step1OrgStatusFeedback) {
              DOM.step1OrgStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';
              DOM.step1OrgStatusFeedback.style.color = '#FCA5A5';
              DOM.step1OrgStatusFeedback.innerHTML = `❌ ${res.error || 'Failed to create repository'}`;
            }
            showToast(res.error || 'Failed to create repository', 'error');
          }
        } catch (err) {
          if (DOM.step1OrgStatusFeedback) {
            DOM.step1OrgStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';
            DOM.step1OrgStatusFeedback.style.color = '#FCA5A5';
            DOM.step1OrgStatusFeedback.innerHTML = `❌ Error: ${err.message}`;
          }
        } finally {
          DOM.btnStep1CreateRepo.disabled = false;
          DOM.btnStep1CreateRepo.innerHTML = '<span>🚀 Create Repo</span>';
        }
      });
    }

    if (DOM.newProjGhOwnerSelect) {
      DOM.newProjGhOwnerSelect.addEventListener('change', () => {
        const val = DOM.newProjGhOwnerSelect.value;
        if (!val) return;
        if (DOM.newProjGhOwner) DOM.newProjGhOwner.value = val;
        if (DOM.newProjGhRepo) DOM.newProjGhRepo.value = `${val}.github.io`;
      });
    }

    if (DOM.btnVerifyGhToken) {
      DOM.btnVerifyGhToken.addEventListener('click', async () => {
        DOM.btnVerifyGhToken.disabled = true;
        DOM.btnVerifyGhToken.innerHTML = '<span>⏳ Querying GitHub...</span>';
        await loadGithubAccounts();
        DOM.btnVerifyGhToken.disabled = false;
        DOM.btnVerifyGhToken.innerHTML = '<span>⚡ Test Token &amp; Detect Orgs</span>';
        showToast('GitHub token tested and accounts detected.', 'info');
      });
    }

    // Check / Create Organization Action

    if (DOM.btnCheckCreateOrg) {

      DOM.btnCheckCreateOrg.addEventListener('click', async () => {

        const orgName = (DOM.cfgGithubOwner.value || '').trim();

        let token = (DOM.cfgGithubToken.value || '').trim();

        if (token.includes('****')) token = '';

        if (!orgName) {

          showToast('Please enter an Organization name first.', 'error');

          DOM.cfgGithubOwner.focus();

          return;

        }



        DOM.btnCheckCreateOrg.disabled = true;

        DOM.btnCheckCreateOrg.innerHTML = '<span>⏳ Querying GitHub API...</span>';

        DOM.orgStatusFeedback.style.display = 'block';

        DOM.orgStatusFeedback.style.background = 'rgba(59, 130, 246, 0.15)';

        DOM.orgStatusFeedback.style.color = '#93C5FD';

        DOM.orgStatusFeedback.innerHTML = `Checking status of organization <strong>${orgName}</strong> on GitHub...`;

        DOM.linkOpenGithubOrg.style.display = 'none';



        try {

          const res = await api('/api/github/check-org', 'POST', { org: orgName, token: token });

          if (res.exists) {

            DOM.orgStatusFeedback.style.background = 'rgba(16, 185, 129, 0.18)';

            DOM.orgStatusFeedback.style.color = '#34D399';

            DOM.orgStatusFeedback.innerHTML = `✅ <strong>${res.message}</strong><br><small>Plan: ${res.details?.plan || 'Free'} | Verified repository container ready.</small>`;

            DOM.cfgGithubIsOrg.checked = true;

            DOM.linkOpenGithubOrg.style.display = 'none';

            showToast(`Organization '${orgName}' is ready!`, 'success');

          } else {

            DOM.orgStatusFeedback.style.background = 'rgba(245, 158, 11, 0.18)';

            DOM.orgStatusFeedback.style.color = '#FCD34D';

            DOM.orgStatusFeedback.innerHTML = `⚠️ <strong>${res.message}</strong><br><small style="color:#E2E8F0;">${res.api_limitation}</small>`;

            DOM.linkOpenGithubOrg.style.display = 'inline-flex';

            DOM.linkOpenGithubOrg.href = res.create_web_url || 'https://github.com/account/organizations/new?plan=free';

            showToast(`Organization '${orgName}' needs to be created on GitHub.`, 'warning');

          }

        } catch (err) {

          DOM.orgStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';

          DOM.orgStatusFeedback.style.color = '#FCA5A5';

          DOM.orgStatusFeedback.innerHTML = `❌ Error: ${err.message}`;

        } finally {

          DOM.btnCheckCreateOrg.disabled = false;

          DOM.btnCheckCreateOrg.innerHTML = '<span>🏢 Check / Create Organization</span>';

        }

      });

    }



    if (DOM.selectGithubAccount) {

      DOM.selectGithubAccount.addEventListener('change', () => {

        const val = DOM.selectGithubAccount.value;

        if (!val) return;

        const opt = DOM.selectGithubAccount.selectedOptions[0];

        const isOrg = opt ? opt.dataset.isOrg === 'true' : false;

        DOM.cfgGithubOwner.value = val;

        DOM.cfgGithubIsOrg.checked = isOrg;

        updateRootDomainPreview();

        showToast(`Selected: ${val}`, 'info');

      });

    }



    if (DOM.btnRefreshOrgs) {

      DOM.btnRefreshOrgs.addEventListener('click', async () => {

        DOM.selectGithubAccount.innerHTML = '<option value="">🔄 Refreshing organizations...</option>';

        await loadGithubAccounts();

        showToast('Organizations list refreshed from GitHub.', 'info');

      });

    }



    if (DOM.btnCreateRepoNow) {

      DOM.btnCreateRepoNow.addEventListener('click', async () => {

        const owner = (DOM.cfgGithubOwner.value || '').trim();

        const repo = (DOM.cfgGithubRepo.value || '').trim();

        const isOrg = DOM.cfgGithubIsOrg.checked;

        let token = (DOM.cfgGithubToken.value || '').trim();

        if (token.includes('****')) token = '';



        if (!owner || !repo) {

          showToast('Please enter/select Organization and Repository Name first.', 'error');

          return;

        }



        DOM.btnCreateRepoNow.disabled = true;

        DOM.btnCreateRepoNow.innerHTML = '<span>⏳ Creating Repo on GitHub...</span>';

        DOM.orgStatusFeedback.style.display = 'block';

        DOM.orgStatusFeedback.style.background = 'rgba(59, 130, 246, 0.15)';

        DOM.orgStatusFeedback.style.color = '#93C5FD';

        DOM.orgStatusFeedback.innerHTML = `Creating repository <strong>${owner}/${repo}</strong> on GitHub...`;



        try {

          const res = await api('/api/github/create-repo', 'POST', {

            owner,

            repo,

            is_org: isOrg,

            token,

          });



          if (res.success) {

            DOM.orgStatusFeedback.style.background = 'rgba(16, 185, 129, 0.18)';

            DOM.orgStatusFeedback.style.color = '#34D399';

            DOM.orgStatusFeedback.innerHTML = `🎉 <strong>${res.message}</strong><br><a href="${res.repo_url}" target="_blank" style="color:#60A5FA;text-decoration:underline;font-weight:600;">View ${res.repo} on GitHub ↗</a> | Pages URL: <strong>${res.pages_url}</strong>`;

            showToast(`Repository ${res.repo} ready!`, 'success');

            refreshSystem();

          } else {

            DOM.orgStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';

            DOM.orgStatusFeedback.style.color = '#FCA5A5';

            DOM.orgStatusFeedback.innerHTML = `❌ Failed: ${res.error}`;

            showToast(`Failed: ${res.error}`, 'error');

          }

        } catch (err) {

          DOM.orgStatusFeedback.style.background = 'rgba(239, 68, 68, 0.18)';

          DOM.orgStatusFeedback.style.color = '#FCA5A5';

          DOM.orgStatusFeedback.innerHTML = `❌ Network Error: ${err.message}`;

          showToast(`Error: ${err.message}`, 'error');

        } finally {

          DOM.btnCreateRepoNow.disabled = false;

          DOM.btnCreateRepoNow.innerHTML = '<span>🚀 Create Repository Now</span>';

        }

      });

    }



    // Settings Submit

    DOM.settingsForm.addEventListener('submit', async (e) => {

      e.preventDefault();

      try {

        const tokenInput = DOM.cfgGithubToken.value.trim();

        const ghPayload = {
          branch: DOM.cfgGithubBranch ? DOM.cfgGithubBranch.value.trim() : 'main',
          base_path: DOM.cfgGithubBasePath ? DOM.cfgGithubBasePath.value.trim() : '',
        };
        // Only include owner/repo if explicitly present and not empty
        if (DOM.cfgGithubOwner && DOM.cfgGithubOwner.value.trim()) {
          ghPayload.owner = DOM.cfgGithubOwner.value.trim();
        }
        if (DOM.cfgGithubRepo && DOM.cfgGithubRepo.value.trim()) {
          ghPayload.repo = DOM.cfgGithubRepo.value.trim();
        }
        if (DOM.cfgGithubIsOrg) {
          ghPayload.is_org = DOM.cfgGithubIsOrg.checked;
        }

        if (tokenInput && !tokenInput.includes('****')) {

          ghPayload.token = tokenInput;

        }



        await api('/api/config', 'POST', {

          github: ghPayload,

        });

        showToast('GitHub configuration saved.', 'success');
        await loadGithubAccounts();

        if (tokenInput && !tokenInput.includes('****')) {

          DOM.cfgGithubToken.value = '';

        }

        await refreshSystem();

      } catch (err) {

        showToast(`Save error: ${err.message}`, 'error');

      }

    });



    // Build Options Submit

    DOM.buildOptionsForm.addEventListener('submit', async (e) => {

      e.preventDefault();

      try {

        await api('/api/config', 'POST', {

          build: {

            theme: DOM.cfgTheme.value,

            routing_mode: DOM.cfgRoutingMode.value,

            output_dir: DOM.cfgOutputDir.value.trim(),

          },

          ingestion: {

            wp_api_url: DOM.cfgWpApiUrl.value.trim(),

          },

          branding: {

            brand_name: DOM.cfgBrandName ? DOM.cfgBrandName.value.trim() : 'Anna Deco',

            tagline: DOM.cfgBrandTagline ? DOM.cfgBrandTagline.value.trim() : '',

            author_name: DOM.cfgAuthorName ? DOM.cfgAuthorName.value.trim() : 'Anna Lindqvist',

            author_bio: DOM.cfgAuthorBio ? DOM.cfgAuthorBio.value.trim() : '',

            enable_toc: DOM.cfgEnableToc ? DOM.cfgEnableToc.checked : true,

            enable_faq: DOM.cfgEnableFaq ? DOM.cfgEnableFaq.checked : true,

            enable_eeat: DOM.cfgEnableEeat ? DOM.cfgEnableEeat.checked : true,

          },

        });

        showToast('Generation settings updated.', 'success');

        refreshSystem();

      } catch (err) {

        showToast(`Save error: ${err.message}`, 'error');

      }

    });



    // Reusable Logo Upload Handler

    async function uploadCustomLogo(file) {

      if (!file) return;

      if (file.size > 5 * 1024 * 1024) {

        showToast('Image file exceeds 5MB limit.', 'error');

        return;

      }

      const reader = new FileReader();

      reader.onload = async () => {

        const base64Data = reader.result;

        try {

          showToast('Uploading custom logo...', 'info');

          const res = await api('/api/upload-logo', 'POST', {

            data: base64Data,

            brand_name: DOM.cfgBrandName ? DOM.cfgBrandName.value.trim() : 'Anna Deco',

            tagline: DOM.cfgBrandTagline ? DOM.cfgBrandTagline.value.trim() : '',

          });



          if (res.success) {

            showToast('Custom logo uploaded & active across all themes!', 'success');

            updateLogoPreview(res.logo_url, res.brand_name, res.tagline);

            triggerPreview();

          } else {

            showToast(`Logo Upload Failed: ${res.error || 'Unknown error'}`, 'error');

          }

        } catch (err) {

          showToast(`Upload Error: ${err.message}`, 'error');

        }

      };

      reader.readAsDataURL(file);

    }



    // Reusable Logo Reset Handler

    async function resetCustomLogo() {

      if (!confirm('Revert to the default luxury vector SVG emblem?')) return;

      try {

        const res = await api('/api/upload-logo', 'POST', { reset: true });

        if (res.success) {

          showToast('Reset to default vector SVG emblem.', 'info');

          updateLogoPreview('', DOM.cfgBrandName ? DOM.cfgBrandName.value : 'Anna Deco');

          if (DOM.logoFileInput) DOM.logoFileInput.value = '';

          if (DOM.quickLogoFileInput) DOM.quickLogoFileInput.value = '';

          if (DOM.previewLogoFileInput) DOM.previewLogoFileInput.value = '';

          triggerPreview();

        }

      } catch (err) {

        showToast(`Reset Error: ${err.message}`, 'error');

      }

    }



    // Wire file inputs across all locations (Branding form, Theme gallery, Preview sidebar)

    if (DOM.logoFileInput) {

      DOM.logoFileInput.addEventListener('change', (e) => uploadCustomLogo(e.target.files[0]));

    }

    if (DOM.quickLogoFileInput) {

      DOM.quickLogoFileInput.addEventListener('change', (e) => uploadCustomLogo(e.target.files[0]));

    }

    if (DOM.previewLogoFileInput) {

      DOM.previewLogoFileInput.addEventListener('change', (e) => uploadCustomLogo(e.target.files[0]));

    }



    // Wire reset buttons across all locations

    if (DOM.btnResetLogo) {

      DOM.btnResetLogo.addEventListener('click', resetCustomLogo);

    }

    if (DOM.quickBtnResetLogo) {

      DOM.quickBtnResetLogo.addEventListener('click', resetCustomLogo);

    }

    if (DOM.previewBtnResetLogo) {

      DOM.previewBtnResetLogo.addEventListener('click', resetCustomLogo);

    }



    // Source Type Switcher

    DOM.ingestSourceType.addEventListener('change', () => {

      const val = DOM.ingestSourceType.value;

      if (val === 'url_list') {

        DOM.groupSitemapUrl.style.display = 'none';

        DOM.groupUrlList.style.display = 'block';

      } else {

        DOM.groupSitemapUrl.style.display = 'block';

        DOM.groupUrlList.style.display = 'none';

      }

    });



    // Scan Sitemap

    DOM.scanSitemapBtn.addEventListener('click', async () => {

      try {

        appendTerminalLog('Scanning WordPress sitemap index...', 'info');

        const res = await api('/api/sitemap/scan', 'POST', {

          url_or_list: DOM.ingestSitemapUrl.value.trim(),

        });

        showToast(`Discovered ${res.discovered_count} post URLs.`, 'info');

        appendTerminalLog(`Scan complete: ${res.discovered_count} URLs located.`, 'success');

      } catch (err) {

        showToast(`Scan failed: ${err.message}`, 'error');

      }

    });



    // Run Ingestion

    DOM.ingestionForm.addEventListener('submit', async (e) => {

      e.preventDefault();

      const sourceType = DOM.ingestSourceType.value;

      const urlOrList = sourceType === 'url_list' ? DOM.ingestUrlList.value : DOM.ingestSitemapUrl.value;



      try {

        appendTerminalLog(`Running ingestion & manifest diffing (source=${sourceType})...`, 'info');

        const res = await api('/api/ingest', 'POST', {

          source_type: sourceType,

          url_or_list: urlOrList,

          max_posts: parseInt(DOM.ingestMaxPosts.value, 10),

          download_images: DOM.ingestDownloadImages.checked,

          force_full_resync: DOM.ingestForceResync.checked,

        });



        const sum = res.summary || {};

        const counts = sum.counts || {};

        DOM.diffNewCount.textContent = counts.new || 0;

        DOM.diffUpdatedCount.textContent = counts.updated || 0;

        DOM.diffSyncedCount.textContent = counts.synced || 0;

        DOM.diffResultsBox.style.display = 'block';



        DOM.diffSummaryTableBody.innerHTML = '';

        (sum.new_posts || []).forEach((p) => addDiffRow(p.slug, p.title, 'NEW', 'badge-new'));

        (sum.updated_posts || []).forEach((p) => addDiffRow(p.slug, p.title, 'UPDATED', 'badge-updated'));

        (sum.synced_posts || []).forEach((p) => addDiffRow(p.slug, p.title, 'SYNCED', 'badge-synced'));



        showToast(`Ingestion finished: ${counts.total || 0} total posts processed.`, 'success');

        appendTerminalLog(`Ingested: ${counts.new} new, ${counts.updated} updated, ${counts.synced} synced.`, 'success');

        refreshSystem();

      } catch (err) {

        showToast(`Ingestion error: ${err.message}`, 'error');

        appendTerminalLog(`Ingestion failure: ${err.message}`, 'error');

      }

    });



    function addDiffRow(slug, title, status, badgeClass) {

      const tr = document.createElement('tr');

      tr.innerHTML = `

        <td><span class="badge ${badgeClass}">${status}</span></td>

        <td><code>${escapeHtml(slug)}</code></td>

        <td>${escapeHtml(title)}</td>

      `;

      DOM.diffSummaryTableBody.appendChild(tr);

    }



    // Search and Filters

    DOM.postSearchInput.addEventListener('input', () => refreshPosts());

    DOM.postCategoryFilter.addEventListener('change', () => refreshPosts());

    DOM.postStatusFilter.addEventListener('change', () => refreshPosts());



    // Modal Events

    if (DOM.addTakeawayBtn) DOM.addTakeawayBtn.addEventListener('click', () => addTakeawayInput());

    if (DOM.addChecklistBtn) DOM.addChecklistBtn.addEventListener('click', () => addChecklistInput());

    DOM.closeModalBtn.addEventListener('click', () => DOM.postEditModal.classList.remove('active'));

    DOM.cancelEditBtn.addEventListener('click', () => DOM.postEditModal.classList.remove('active'));

    DOM.editPostForm.addEventListener('submit', handlePostSave);



    // Preview Events

    DOM.previewPostSelect.addEventListener('change', () => {

      state.selectedPostSlug = DOM.previewPostSelect.value;

      const post = state.posts.find((p) => p.slug === state.selectedPostSlug);

      if (post) {

        DOM.previewLiveTitle.value = post.title || '';

        if (DOM.previewLiveExcerpt) DOM.previewLiveExcerpt.value = post.excerpt || '';

      }

      triggerPreview();

    });



    DOM.previewThemeSelect.addEventListener('change', () => triggerPreview());

    DOM.previewRoutingSelect.addEventListener('change', () => triggerPreview());



    if (DOM.previewLiveTitle) {
      DOM.previewLiveTitle.addEventListener('input', () => {
        clearTimeout(state.previewDebounceTimer);
        state.previewDebounceTimer = setTimeout(triggerPreview, 350);
      });
    }

    if (DOM.previewLiveExcerpt) {
      DOM.previewLiveExcerpt.addEventListener('input', () => {
        clearTimeout(state.previewDebounceTimer);
        state.previewDebounceTimer = setTimeout(triggerPreview, 350);
      });
    }

    if (DOM.refreshPreviewBtn) DOM.refreshPreviewBtn.addEventListener('click', () => triggerPreview());



    // Viewport Width Switching

    DOM.viewportBtns.forEach((btn) => {

      btn.addEventListener('click', () => {

        DOM.viewportBtns.forEach((b) => b.classList.remove('active'));

        btn.classList.add('active');

        DOM.previewIframe.style.width = btn.getAttribute('data-width');

      });

    });



    // =========================================================================

    // THEME & ROUTING ARCHITECTURE VISUAL PREVIEW GALLERY

    // =========================================================================



    // Theme Card Selection Handler

    document.querySelectorAll('.theme-card').forEach((card) => {

      card.addEventListener('click', (e) => {

        if (e.target.closest('.btn-preview-theme')) return; // handled by preview modal trigger

        const themeKey = card.dataset.theme;

        document.querySelectorAll('.theme-card').forEach((c) => c.classList.remove('active'));

        card.classList.add('active');

        if (DOM.cfgTheme) DOM.cfgTheme.value = themeKey;

        if (DOM.previewThemeSelect) DOM.previewThemeSelect.value = themeKey;

        triggerPreview();

      });

    });



    // Routing Card Selection Handler

    document.querySelectorAll('.routing-card').forEach((card) => {

      card.addEventListener('click', () => {

        const routeKey = card.dataset.routing;

        document.querySelectorAll('.routing-card').forEach((c) => c.classList.remove('active'));

        card.classList.add('active');

        if (DOM.cfgRoutingMode) DOM.cfgRoutingMode.value = routeKey;

        if (DOM.previewRoutingSelect) DOM.previewRoutingSelect.value = routeKey;

        triggerPreview();

      });

    });



    // Open Fullscreen Template Preview Modal

    async function openTemplateModal(themeKey, routingKey, defaultView = 'hub') {

      const theme = themeKey || (DOM.cfgTheme && DOM.cfgTheme.value) || 'nordic-studio';

      const routing = routingKey || (DOM.cfgRoutingMode && DOM.cfgRoutingMode.value) || 'single';

      state.modalActiveTheme = theme;

      state.modalActiveRouting = routing;

      state.modalActiveView = defaultView || 'hub';

      // Synchronize modal view toggle buttons
      document.querySelectorAll('.modal-view-btn').forEach((btn) => {
        if (btn.dataset.view === state.modalActiveView) {
          btn.classList.add('active', 'btn-primary');
          btn.classList.remove('btn-secondary');
        } else {
          btn.classList.remove('active', 'btn-primary');
          btn.classList.add('btn-secondary');
        }
      });



      const themeNames = {

        'editorial-warm': 'Model 1 · Kinfolk Journal',

        'nordic-studio': 'The Nordroom (Scandinavian Minimalist)',

        'pinterest-mag': 'Pinterest Mag (Visual Discovery & Pin Focus)',

      };

      const routingNames = {

        'single': 'Single Slug (/<slug>/)',

        'category_slug': 'Category Slug (/<category>/<slug>/)',

        'parent_slug': 'Parent Slug (/<parent>/<slug>/)',

        'silo_nested': 'Silo Nested (/guides/<parent>/<slug>/)',

      };



      if (DOM.templateModalThemeBadge) {

        DOM.templateModalThemeBadge.textContent = themeNames[theme] || theme;

      }

      if (DOM.templateModalRoutingBadge) {

        DOM.templateModalRoutingBadge.textContent = routingNames[routing] || routing;

      }



      if (DOM.templatePreviewModal) {

        DOM.templatePreviewModal.classList.add('active');

      }



      try {

        const samplePayload = {

          theme,

          routing_mode: routing,

          view_mode: state.modalActiveView,

        };

        if (state.modalActiveView === 'post') {
          samplePayload.post = {

            slug: 'modern-room-styling-guide',

            title: 'Modern Scandinavian Living Room Design: 15 Warm Minimalist Ideas',

            excerpt: 'Transform your main living space with organic textures, functional hidden storage, and warm lighting layers designed for everyday comfort.',

            category: 'Living Room Styling',

            category_slug: 'living-room',

            parent_slug: 'home-organization',

            date: '2026-11-02',

            takeaways: [

              'Balanced Room Proportions: Anchor your layout with clean-lined low profile seating.',

              'Layered Textures: Blend natural oak, boucle, and linen for Scandinavian warmth.',

              'Intentional Lighting: Use 3 light sources at varying heights to eliminate dark corners.',

            ],

            checklist: [

              { id: 'step-1', text: 'Measure room footprint and map primary natural light windows' },

              { id: 'step-2', text: 'Select foundational neutral furniture pieces (boucle, warm oak)' },

              { id: 'step-3', text: 'Install warm-toned 2700K ambient and task lighting fixtures' },

            ],

          };
        }



        const res = await api('/api/preview', 'POST', samplePayload);

        if (res.html && DOM.templateModalIframe) {

          DOM.templateModalIframe.srcdoc = res.html;

        }

      } catch (err) {

        showToast(`Template preview render failed: ${err.message}`, 'error');

      }

    }



    // Modal View Toggle Triggers
    document.querySelectorAll('.modal-view-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const view = btn.dataset.view;
        if (!view) return;
        openTemplateModal(state.modalActiveTheme, state.modalActiveRouting, view);
      });
    });

    // Modal Close Triggers

    if (DOM.closeTemplateModalBtn) {

      DOM.closeTemplateModalBtn.addEventListener('click', () => {

        if (DOM.templatePreviewModal) DOM.templatePreviewModal.classList.remove('active');

      });

    }



    if (DOM.templatePreviewModal) {

      DOM.templatePreviewModal.addEventListener('click', (e) => {

        if (e.target === DOM.templatePreviewModal) {

          DOM.templatePreviewModal.classList.remove('active');

        }

      });

    }



    window.addEventListener('keydown', (e) => {

      if (e.key === 'Escape' && DOM.templatePreviewModal && DOM.templatePreviewModal.classList.contains('active')) {

        DOM.templatePreviewModal.classList.remove('active');

      }

    });



    // Viewport Width Switching inside Modal

    document.querySelectorAll('.modal-vp-btn').forEach((btn) => {

      btn.addEventListener('click', () => {

        document.querySelectorAll('.modal-vp-btn').forEach((b) => b.classList.remove('active'));

        btn.classList.add('active');

        if (DOM.templateModalIframe) {

          DOM.templateModalIframe.style.width = btn.getAttribute('data-width');

        }

      });

    });



    // "Apply This Theme" inside Preview Modal

    if (DOM.applyTemplateThemeBtn) {

      DOM.applyTemplateThemeBtn.addEventListener('click', () => {

        const chosen = state.modalActiveTheme || 'nordic-studio';

        if (DOM.cfgTheme) DOM.cfgTheme.value = chosen;

        if (DOM.previewThemeSelect) DOM.previewThemeSelect.value = chosen;

        document.querySelectorAll('.theme-card').forEach((c) => {

          if (c.dataset.theme === chosen) c.classList.add('active');

          else c.classList.remove('active');

        });

        if (DOM.templatePreviewModal) DOM.templatePreviewModal.classList.remove('active');

        showToast(`Theme applied: ${chosen}. Click 'Save Generation Settings' to persist.`, 'success');

      });

    }



    // Theme Card Direct Preview Buttons

    document.querySelectorAll('.btn-preview-theme').forEach((btn) => {

      btn.addEventListener('click', (e) => {

        e.stopPropagation();

        const theme = btn.dataset.theme;

        openTemplateModal(theme);

      });

    });



    // Header "Open Fullscreen Template Preview" Button

    if (DOM.btnOpenThemePreview) {

      DOM.btnOpenThemePreview.addEventListener('click', () => {

        openTemplateModal(DOM.cfgTheme?.value, DOM.cfgRoutingMode?.value);

      });

    }



    // Asset Sync Trigger

    async function handleSyncAssets() {

      try {

        showToast('Syncing all post image assets to project...', 'info');

        appendTerminalLog('[ASSETS] Scanning posts and downloading missing featured images to assets/images/...', 'info');

        const res = await api('/api/assets/sync', 'POST', { force: false });

        if (res.success) {

          showToast(`Saved ${res.total} image assets to project (${res.downloaded} downloaded, ${res.generated_svg} SVGs)!`, 'success');

          appendTerminalLog(`[ASSETS] Completed: ${res.total} image assets verified in assets/images/ (${res.downloaded} newly downloaded, ${res.generated_svg} SVGs generated).`, 'info');

          await refreshSystem();

          await refreshPosts();

        } else {

          showToast(res.error || 'Failed to sync assets', 'error');

        }

      } catch (err) {

        showToast(`Asset Sync Error: ${err.message}`, 'error');

        appendTerminalLog(`[ERROR] Asset sync failed: ${err.message}`, 'error');

      }

    }

    if (DOM.syncAssetsBtn) DOM.syncAssetsBtn.addEventListener('click', handleSyncAssets);

    if (DOM.syncAssetsDeployBtn) DOM.syncAssetsDeployBtn.addEventListener('click', handleSyncAssets);

    if (DOM.syncAssetsSettingsBtn) DOM.syncAssetsSettingsBtn.addEventListener('click', handleSyncAssets);



    // WebP Image Optimization Trigger

    if (DOM.optimizeWebpBtn) {

      DOM.optimizeWebpBtn.addEventListener('click', async () => {

        try {

          showToast('Optimizing images in assets/images/ to standard WebP...', 'info');

          appendTerminalLog('[WEBP] Optimizing images to standard 16:10 WebP...', 'info');

          const res = await api('/api/images/optimize', 'POST', { quality: 82 });

          if (res.success) {

            const stats = res.stats || {};

            const msg = `WebP complete: ${stats.converted || 0} images converted (${stats.percent_reduction || 0}% space saved).`;

            showToast(msg, 'success');

            appendTerminalLog(`[WEBP SUCCESS] ${msg}`, 'success');

            refreshSystem();

          } else {

            showToast('Optimization failed', 'error');

          }

        } catch (err) {

          showToast(`Optimization error: ${err.message}`, 'error');

          appendTerminalLog(`[WEBP ERROR] ${err.message}`, 'error');

        }

      });

    }



    // Build Trigger

    async function executeBuild() {

      try {

        appendTerminalLog('[BUILD] Starting static compilation to disk...', 'info');

        const isCf = (typeof currentPlatformMode !== 'undefined' && currentPlatformMode === 'cloudflare') || (state.activePlatform === 'cloudflare') || (!document.getElementById('workspaceCloudflare')?.classList.contains('hidden') && document.getElementById('workspaceCloudflare')?.style.display !== 'none');
        const activePlatform = isCf ? 'cloudflare' : 'github';
        const workerInput = document.getElementById('cfgCfProjectName')?.value?.trim();
        const activeProject = isCf 
          ? (workerInput || DOM.cockpitCfWorker?.textContent?.trim() || 'gardenhome')
          : (DOM.cockpitGhOwner?.textContent?.trim() || 'annadeco');

        const res = await api('/api/build', 'POST', { 
          clean: true,
          target_cloud: activePlatform,
          project_name: activeProject
        });

        const assetMsg = res.assets_copied ? ` (${res.assets_copied} image assets copied)` : '';

        showToast(`Build complete: ${res.files_generated} files generated${assetMsg}.`, 'success');

        appendTerminalLog(`[BUILD SUCCESS] Generated ${res.files_generated} static files in ${res.output_dir}${assetMsg}`, 'success');

        refreshSystem();

      } catch (err) {

        showToast(`Build failed: ${err.message}`, 'error');

        appendTerminalLog(`[BUILD ERROR] ${err.message}`, 'error');

      }

    }

    if (DOM.triggerBuildBtn) DOM.triggerBuildBtn.addEventListener('click', executeBuild);

    if (DOM.quickBuildBtn) DOM.quickBuildBtn.addEventListener('click', executeBuild);



    // Deployment Log Poller & Terminal Filter State

    let currentFilter = 'all';

    let cachedLogs = [];



    function renderTerminalLogs(logs) {

      cachedLogs = logs || [];

      if (!DOM.terminalBody) return;

      DOM.terminalBody.innerHTML = '';

      cachedLogs.forEach((line) => {

        const lower = line.toLowerCase();

        if (currentFilter === 'cf' && !line.includes('[CLOUDFLARE]')) return;

        if (currentFilter === 'gh' && !line.includes('[GITHUB]') && !line.includes('[DEPLOY]') && !line.includes('GitHub')) return;

        if (currentFilter === 'build' && !line.includes('[BUILD]') && !line.includes('[ASSETS]') && !line.includes('[WEBP]')) return;



        let cls = 'log-info';

        if (lower.includes('error') || lower.includes('fail') || lower.includes('fatal')) cls = 'log-error';

        else if (lower.includes('success') || lower.includes('deployed') || lower.includes('verified')) cls = 'log-success';



        const div = document.createElement('div');

        div.className = cls;

        div.textContent = line;

        DOM.terminalBody.appendChild(div);

      });

      DOM.terminalBody.scrollTop = DOM.terminalBody.scrollHeight;

    }



    function startLogPolling(onFinished) {

      if (state.logPollInterval) clearInterval(state.logPollInterval);

      state.logPollInterval = setInterval(async () => {

        try {

          const statusRes = await api('/api/deploy/logs');

          if (statusRes.logs && statusRes.logs.length) {

            renderTerminalLogs(statusRes.logs);

          }

          if (statusRes.status === 'success' || statusRes.status === 'failed') {

            clearInterval(state.logPollInterval);

            state.logPollInterval = null;

            if (onFinished) onFinished(statusRes.status === 'success');

          }

        } catch (e) {}

      }, 1200);

    }



    // Terminal Filter Buttons

    if (DOM.termFilterBtns) {

      DOM.termFilterBtns.forEach((btn) => {

        btn.addEventListener('click', () => {

          DOM.termFilterBtns.forEach((b) => b.classList.remove('active'));

          btn.classList.add('active');

          currentFilter = btn.getAttribute('data-filter') || 'all';

          renderTerminalLogs(cachedLogs);

        });

      });

    }



    // Copy Terminal Logs

    if (DOM.copyLogsBtn) {

      DOM.copyLogsBtn.addEventListener('click', () => {

        const text = DOM.terminalBody ? DOM.terminalBody.innerText : '';

        if (navigator.clipboard && text) {

          navigator.clipboard.writeText(text).then(() => {

            showToast('Deployment logs copied to clipboard!', 'success');

          }).catch(() => {

            showToast('Unable to copy logs to clipboard.', 'error');

          });

        }

      });

    }



    // Deploy Trigger: GitHub Pages

    DOM.triggerDeployBtn.addEventListener('click', async () => {

      const dryRun = DOM.deployDryRun.checked;

      const ghOwner = DOM.cockpitGhOwner?.textContent?.trim() || 'annadeco';
      try {

        appendTerminalLog(`[GITHUB] Initiating Pages deployment (owner=${ghOwner}, dry_run=${dryRun})...`, 'info');

        const res = await api('/api/deploy', 'POST', { 
          dry_run: dryRun,
          project_name: ghOwner
        });

        showToast(res.message, 'info');



        startLogPolling((success) => {

          if (success) {

            showToast('GitHub Pages deployment completed successfully!', 'success');

          } else {

            showToast('GitHub deployment encountered errors.', 'error');

          }

          refreshSystem();

        });

      } catch (err) {

        showToast(`Deploy error: ${err.message}`, 'error');

        appendTerminalLog(`[GITHUB ERROR] ${err.message}`, 'error');

      }

    });



    // Deploy Trigger: Cloudflare Workers

    if (DOM.triggerCfDeployBtn) {

      DOM.triggerCfDeployBtn.addEventListener('click', async () => {

        const dryRun = DOM.deployCfDryRun ? DOM.deployCfDryRun.checked : false;

        const workerName = document.getElementById('cfgCfProjectName')?.value?.trim() || DOM.cockpitCfWorker?.textContent?.trim() || 'gardenhome';
        try {

          appendTerminalLog(`[CLOUDFLARE] Initiating Workers deployment (Worker Name=${workerName}, dry_run=${dryRun})...`, 'info');

          const res = await api('/api/cloudflare/deploy', 'POST', { 
            dry_run: dryRun,
            subdomain: workerName,
            worker_name: workerName
          });

          showToast(res.message, 'info');



          startLogPolling((success) => {

            if (success) {

              showToast('Cloudflare Workers deployment completed successfully!', 'success');

            } else {

              showToast('Cloudflare Workers deployment encountered errors.', 'error');

            }

            refreshSystem();

          });

        } catch (err) {

          showToast(`Cloudflare Deploy error: ${err.message}`, 'error');

          appendTerminalLog(`[CLOUDFLARE ERROR] ${err.message}`, 'error');

        }

      });

    }



    // Deploy Trigger: Dual Deployment (Both Cloudflare & GitHub)

    if (DOM.triggerDualDeployBtn) {

      DOM.triggerDualDeployBtn.addEventListener('click', async () => {

        const dryRun = (DOM.deployDryRun && DOM.deployDryRun.checked) || (DOM.deployCfDryRun && DOM.deployCfDryRun.checked);

        try {

          appendTerminalLog(`[MULTI-CLOUD] Launching Dual Deployment to Cloudflare Workers & GitHub Pages (dry_run=${dryRun})...`, 'info');

          const res = await api('/api/deploy/dual', 'POST', { dry_run: dryRun });

          showToast(res.message, 'info');



          startLogPolling((success) => {

            if (success) {

              showToast('Multi-Cloud Dual Deployment completed successfully!', 'success');

            } else {

              showToast('Dual deployment encountered errors on one or more clouds.', 'error');

            }

            refreshSystem();

          });

        } catch (err) {

          showToast(`Dual Deploy error: ${err.message}`, 'error');

          appendTerminalLog(`[MULTI-CLOUD ERROR] ${err.message}`, 'error');

        }

      });

    }



    // Clear Terminal Logs

    DOM.clearLogsBtn.addEventListener('click', () => {

      cachedLogs = [];

      DOM.terminalBody.innerHTML = '<div class="log-info">[INFO] Terminal log cleared.</div>';

    });

  }



  function escapeHtml(str) {

    if (!str) return '';

    return String(str)

      .replace(/&/g, '&amp;')

      .replace(/</g, '&lt;')

      .replace(/>/g, '&gt;')

      .replace(/"/g, '&quot;')

      .replace(/'/g, '&#039;');

  }



  // Initialize Application

  window.addEventListener('DOMContentLoaded', () => {

    initTabs();

    initPlatformDivision();

    setActivePlatformView('cf');

    switchTab('tab-ingest');

    initListeners();

    initModelSwitcher();

    initProjectSystem();

    refreshSystem();

  });

})();

