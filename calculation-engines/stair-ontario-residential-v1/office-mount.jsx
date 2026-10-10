import { createRoot } from "react-dom/client";
import { StairCalculator } from "./website-source/components/useful-tools/StairCalculator.tsx";

const node = document.querySelector("[data-stair-calculator]");
createRoot(node).render(<StairCalculator />);
