/**
 * Touchline Ledger app shell: persistent workspace navigation, warm paper canvas,
 * pitch-green brand, signal-orange actions, and restrained motion.
 */
import { Toaster } from "@/components/ui/sonner";
import ErrorBoundary from "./components/ErrorBoundary";
import Home from "./pages/Home";

export default function App() {
  return <ErrorBoundary><Toaster position="top-right" /><Home /></ErrorBoundary>;
}
