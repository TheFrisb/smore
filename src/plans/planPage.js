import { initPlanProductTab } from "./PlanProductTab";
import { initCheckoutJs } from "./checkout";

function initPlanPage() {
  initCheckoutJs();
  initPlanProductTab();
}

export { initPlanPage };
