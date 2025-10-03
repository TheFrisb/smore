import { initPlanProductTab } from "./planProductTab";
import { initCheckoutJs } from "./checkout";

function initPlanPage() {
  initCheckoutJs();
  initPlanProductTab();
}

export { initPlanPage };