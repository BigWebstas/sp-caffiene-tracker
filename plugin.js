(() => {
  const p = PluginAPI;
  const openView = () => p.showIndexHtmlAsView();

  p.onReady(() => {
    p.registerHeaderButton?.({
      id: 'caffeine-tracker-header-btn',
      label: 'Caffeine',
      icon: 'coffee',
      onClick: openView,
    });
  });
})();
