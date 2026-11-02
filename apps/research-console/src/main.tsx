import React from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@fontsource/inter/500.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@fontsource/ibm-plex-mono/400.css";
import App from "./App";
import "./styles.css";
const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});
class Boundary extends React.Component<
  { children: React.ReactNode },
  { error: string | null }
> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: Error) {
    return { error: error.message };
  }
  render() {
    return this.state.error ? (
      <main className="fatal">
        <h1>The workspace could not render</h1>
        <p>{this.state.error}</p>
        <button onClick={() => location.reload()}>Reload workspace</button>
      </main>
    ) : (
      this.props.children
    );
  }
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Boundary>
      <QueryClientProvider client={client}>
        <App />
      </QueryClientProvider>
    </Boundary>
  </React.StrictMode>,
);
