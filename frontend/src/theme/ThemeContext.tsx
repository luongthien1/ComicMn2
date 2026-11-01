import { ConfigProvider, theme as antdTheme } from "antd";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import "./theme.css";

export type ThemeMode = "light" | "dark";

const STORAGE_KEY = "comic-theme";

interface ThemeContextValue {
  mode: ThemeMode;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ mode: "light", toggle: () => {} });

function initialMode(): ThemeMode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* localStorage bị chặn — dùng theo hệ điều hành */
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(initialMode);

  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      /* bỏ qua */
    }
  }, [mode]);

  const dark = mode === "dark";
  const toggle = useCallback(() => setMode((m) => (m === "dark" ? "light" : "dark")), []);
  const value = useMemo(() => ({ mode, toggle }), [mode, toggle]);

  return (
    <ThemeContext.Provider value={value}>
      <ConfigProvider
        theme={{
          algorithm: [
            mode === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
            antdTheme.compactAlgorithm,
          ],
          token: {
            fontSize: 15,
            borderRadius: 4,
          },
          components: {
            // Sidebar đơn sắc: nền theo theme, mục đang chọn đảo màu (đen/trắng)
            Layout: {
              siderBg: dark ? "#141414" : "#ffffff",
            },
            Menu: {
              itemBg: "transparent",
              itemColor: dark ? "rgba(255,255,255,0.75)" : "rgba(0,0,0,0.75)",
              itemHoverColor: dark ? "#ffffff" : "#000000",
              itemHoverBg: dark ? "#262626" : "#f5f5f5",
              itemSelectedBg: dark ? "#f0f0f0" : "#000000",
              itemSelectedColor: dark ? "#141414" : "#ffffff",
              itemActiveBg: dark ? "#303030" : "#f0f0f0",
            },
            Table: {
              cellPaddingBlock: 6,
              cellPaddingInline: 10,
            },
          },
        }}
      >
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => useContext(ThemeContext);
