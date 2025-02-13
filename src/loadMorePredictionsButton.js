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

  button.addEventListener("click", function () {
    const button = this;
    const nextPage = button.getAttribute("data-next-page");
    const url = `/api/predictions/?page=${nextPage}`;

    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load more predictions.");
        return response.json();
      })
      .then((data) => {
        data.results.forEach((prediction) => {
          const predictionHtml = `
                              <div class="bg-primary-800/50 backdrop-blur-sm rounded-lg p-6 border border-primary-700/30 hover:border-emerald-500/20 transition-all duration-300 group transform transition-all duration-300 animate-fadeIn">
                        <div class="flex items-center justify-between mb-6">
                            <div class="flex  justify-start items-center space-x-3 text-primary-300">
                                <div class="bg-primary-900/50 p-2 rounded-lg">


                                    <svg class="w-4 h-4 text-white"><use xlink:href="/static/assets/svg/sprite6.svg#soccerIcon"></use></svg>

                                </div>

                                <span class="text-sm text-primary-100">Soccer</span>

                            </div>
                            <div class="flex items-center space-x-2 px-4 py-2 rounded-lg
                                    ${prediction.status === "WON" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/30 text-primary-200"}">

                                        ${
                                          prediction.status === "WON"
                                            ? `
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                             viewBox="0 0 24 24"
                             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round" class="lucide lucide-check w-5 h-5">
                            <path d="M20 6 9 17l-5-5"></path>
                        </svg>`
                                            : `
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
                             viewBox="0 0 24 24"
                             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                             stroke-linejoin="round" class="lucide lucide-x w-5 h-5">
                            <path d="M18 6L6 18"></path>
                            <path d="M6 6L18 18"></path>
                        </svg>`
                                        } 

                                <span class="font-medium">${prediction.status}</span>
                            </div>
                        </div>
                        <div class="mb-6">
                            <div class="text-sm text-primary-300 mb-2">Match:</div>
                            <div class="bg-gradient-to-br rounded-lg border p-6 py-10 shadow-lg relative group-hover:border-secondary-500/30 transition-all duration-300 ${prediction.status === "WON" ? "from-emerald-900/20 to-primary-800/90 border-emerald-500/20" : "from-red-900/20 to-primary-800/90 border-red-500/20"}">
                                <div class="absolute inset-0 bg-gradient-to-r from-secondary-500/0 via-secondary-500/5 to-secondary-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg pointer-events-none"></div>
                                <div
                                        class="absolute top-0 left-1/2 -translate-x-1/2  p-2 rounded-lg text-nowrap"
                                >
                                    <p class="text-sm text-secondary-400 font-bold w-full">${prediction.league}</p>
                                </div>

                                <div class="flex flex-col md:flex-row flex-wrap items-center justify-center md:justify-between gap-x-12 gap-y-4">
                                    <span class="text-xl font-bold text-white whitespace-normal  flex-shrink md:text-left md:w-4/12">${prediction.home_team}</span>
                                    <span class="text-secondary-400 font-medium text-lg px-4 py-2 rounded-full bg-secondary-500/10 border border-secondary-500/20">vs</span>
                                    <span class="text-xl font-bold text-white whitespace-normal flex-shrink md:text-right md:w-4/12">${prediction.away_team}</span>
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-6">
                            <div class="bg-primary-900/50 p-4 rounded-lg border border-primary-700/50">
                                <div class="text-sm text-primary-300 mb-1">Kick-off Date</div>
                                <div class="font-medium text-white">${new Date(
                                  prediction.kickoff_date,
                                ).toLocaleDateString("en-GB", {
                                  day: "2-digit",
                                  month: "2-digit",
                                  year: "numeric",
                                })}</div>
                            </div>
                            <div class="bg-primary-900/50 p-4 rounded-lg border border-primary-700/50">
                                <div class="text-sm text-primary-300 mb-1">Kick-off Time</div>
                                <div class="font-medium text-white">${formatTimeString(prediction.kickoff_time)} (GMT+1)
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <div class="text-sm text-primary-300">Prediction</div>
                                <div class="font-semibold text-lg text-white">${prediction.prediction}</div>
                            </div>
                            <div>
                                <div class="text-right">
                                    <div class="text-sm text-primary-300">Result</div>
                                    <div class="font-semibold text-3xl text-secondary-400">${prediction.result}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-4 pt-4 border-t border-primary-700/30">
                            <div class="flex items-center justify-between">
                                <div class="text-sm text-primary-300">Odds</div>
                                <div class="font-medium text-secondary-400">${prediction.odds}</div> 
                            </div>
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
