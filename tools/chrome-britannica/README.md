# Search Britannica 11 for Chrome

Select text on a web page, right-click, and choose **Search Britannica 11**.
The command sends a `goldendict://` lookup to the local desktop reader. Enable
Britannica in GoldenDict's dictionary toolbar. This uses title lookup, not the
reader's separate full-text search; partial names may require choosing a suggestion.

## Install locally

1. Register GoldenDict as the Windows handler for `goldendict://` links if the
   installed reader has not already done so. The portable reader needs this step.
2. Open `chrome://extensions` and enable **Developer mode**.
3. Click **Load unpacked** and select this directory.
4. On first use, accept Chrome's **Open GoldenDict** prompt.

On Feedly, a small content script preserves Chrome's native right-click menu
when text is selected; it leaves unselected right-clicks alone. After updating
the extension, click its Reload button in `chrome://extensions`, then refresh
the Feedly tab so this script loads before Feedly's menu handlers.

The extension requests the context-menu permission and runs its selection-menu
helper only on Feedly. It sends no web requests and passes only the text selected for this command.
Keep this directory in place while the unpacked extension is installed.

References: [Chrome context menus](https://developer.chrome.com/docs/extensions/reference/api/contextMenus),
[local extension installation](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world),
[GoldenDict URI scheme](https://xiaoyifang.github.io/goldendict-ng/topic_anki/).
