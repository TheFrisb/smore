import { formatIsoString } from "./utils";

const button = document.getElementById("loadMorePredictionsButton");
const predictionsContainer = document.getElementById("predictionsContainer");

function formatTimeString(timeString) {
  const [hours, minutes] = timeString.split(":"); // Split the time string into hours and minutes
  return `${hours}:${minutes}`; // Return the formatted time
}

function initLoadMorePredictionsButton() {
  if (!button || !predictionsContainer) {
    return;
  }
  let show_predictions = true;
  const activeFilter = button.dataset.activeFilter;

  button.addEventListener("click", function () {
    const button = this;
    const nextPage = button.getAttribute("data-next-page");
    let url = `/api/history/predictions/?page=${nextPage}`;

    if (activeFilter && activeFilter !== "All sports") {
      url += `&product=${activeFilter}`;
    }

    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load more predictions.");
        return response.json();
      })
      .then((data) => {
        data.results.forEach((prediction) => {
          const predictionHtml = `
          <div class="${prediction.status == "LOST" ? "bg-red-500/10 border-red-500/50 hover:border-red-500" : "bg-[#14212e] border-emerald-500/50 hover:border-emerald-500"} backdrop-blur-sm rounded-lg p-6 border   transition-all duration-300 group transform animate-fadeIn">
    <div class="flex items-center justify-between mb-6">
        <div class="flex items-center justify-between w-full">
            <div class="flex  justify-start items-center space-x-3 text-primary-300">
                <div class="bg-primary-900/80 p-2 rounded-lg">
                    <svg class="w-4 h-4 text-white"><use xlink:href="/static/assets/svg/sprite11.svg#soccerIcon"></use></svg>
                </div>
                <span class=" text-primary-100">Soccer</span>
            </div>
            ${
              prediction.detailed_analysis !== ""
                ? `<a href="/predictions/${prediction.id}/"
               class="text-secondary-400 flex items-center gap-2 group group-hover:text-primary-300 transition-all duration-300">
                <svg class="w-5 h-5"><use xlink:href="/static/assets/svg/sprite11.svg#arrowRight"></use></svg>
                <p class="font-bold ">View analysis</p>
            </a>`
                : ""
            }
        </div>

    </div>
    <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
            <p class="text-sm text-primary-100 ">Match</p>
            ${prediction.status == "LOST" ? '<div class="flex items-center justify-end gap-2"><p class="text-red-500 font-bold">LOST</p> <svg class="w-5 h-5 text-red-500"><use xlink:href="/static/assets/svg/sprite11.svg#circleX"></use></svg></div>' : '                <div class="flex items-center justify-end gap-2"><p class="text-emerald-500 font-bold">WON</p><svg class="w-5 h-5 text-emerald-500"><use xlink:href="/static/assets/svg/sprite11.svg#circleCheck"></use></svg></div>'}

        </div>
        <div class="bg-[#0D151E] border-primary-700/50 rounded-lg border p-4 shadow-lg relative group-hover:border-secondary-500/30 transition-all duration-300 flex flex-col gap-4">
            <div class="w-full flex items-center justify-center gap-2 relative pb-4">
                <img src="${prediction.match.league.country.logo}" alt="" width="20"
                     style="height: auto!important">
                <p class="text-emerald-500 font-bold">${prediction.match.league.name}</p>
                <div class="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-secondary-500/50 to-transparent"></div>
            </div>

            <div class="flex items-center justify-between">
                <div class="flex flex-col items-start gap-2">
                    <div class="flex items-center justify-start gap-2">
                        <img src="${prediction.match.home_team.logo}" width="24" style="height: auto!important">
                        <p class="text-primary-100 font-bold">${prediction.match.home_team.name}</p>
                    </div>
                    <div class="flex items-center justify-start gap-2">
                        <img src="${prediction.match.away_team.logo}" width="24" style="height: auto!important">
                        <p class="text-primary-100 font-bold">${prediction.match.away_team.name}</p>
                    </div>
                </div>
                <div class="flex items-center justify-end gap-1">
                        <svg class="w-5 h-5 text-emerald-400"><use xlink:href="/static/assets/svg/sprite11.svg#chevronUp"></use></svg>
                        <p class="text-primary-100">Odds</p>
                        <span class="text-emerald-400 font-bold">${prediction.odds}</span>
                    </div>
            </div>
            <div class="flex items-center justify-start gap-1">
                <p class="text-primary-200 text-sm">Date:</p>
                <p class="text-white text-sm">${formatIsoString(prediction.match.kickoff_datetime)}</p> 
            </div>
        </div>
    </div>
        <div class="flex flex-col items-center justify-center">
            <div class="text-sm text-white">Prediction</div>
            <div class="font-semibold text-xl ${prediction.status === "LOST" ? "text-red-500" : "text-emerald-500"} ">${prediction.prediction}</div>
        </div>
</div>
`;
          predictionsContainer.insertAdjacentHTML("beforeend", predictionHtml);
        });

        if (!data.next) {
          button.remove(); // Remove button if no more pages
        } else {
          const nextPageNumber = parseInt(nextPage) + 1;
          button.setAttribute("data-next-page", nextPageNumber);
        }
      })
      .catch((error) => {
        console.error(error);
        alert("Failed to load more predictions.");
      });
  });
}

export default initLoadMorePredictionsButton;
