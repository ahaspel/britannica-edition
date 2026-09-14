chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "britannica11",
      title: "Search Britannica 11",
      contexts: ["selection"]
    });
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "britannica11" || !tab?.id) return;
  const text = info.selectionText?.trim();
  if (!text) return;
  const url = "goldendict://" + encodeURIComponent(text) + "?target=main";
  // An external-app link leaves the source page available in its original tab.
  await chrome.tabs.update(tab.id, {url});
});
