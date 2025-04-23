import { Notyf } from "notyf";
import { formatIsoString } from "../utils";

const loadMoreButton = document.getElementById("loadMorePredictionsButton");
const insertContainer = document.getElementById("predictionsContainer");

let currentPage = 2;

let hasNext = true;
let predictions = [];

let notyf = new Notyf({
  duration: 5000,
  position: {
    x: "right",
    y: "top",
  },
  dismissible: true,
});

function initLoadMorePredictionsButton() {
  if (!loadMoreButton || !insertContainer) {
    return;
  }

  loadMoreButton.addEventListener("click", async () => {
    if (!hasNext || loadMoreButton.disabled) {
      notyf.error("No more predictions to load.");
      return;
    }

    await fetchPredictions();
    if (predictions) {
      predictions.forEach((prediction) => {
        const predictionHtml = createPredictionHtml(prediction);
        insertContainer.insertAdjacentHTML("beforeend", predictionHtml);
      });
    }

    if (!hasNext) {
      loadMoreButton.classList.add("hidden");
      loadMoreButton.disabled = true;
    }
  });
}

function createPredictionHtml(prediction) {
  const object_type = prediction.object_type;

  switch (object_type) {
    case "ticket":
      return createTicketHtml(prediction);
    case "prediction":
      return createSoloPickHtml(prediction);
    default:
      return "";
  }
}

function createTicketHtml(ticket) {
  let html = `
    <div class="${ticket.status == "LOST" ? "bg-red-500/10 border-red-500/50 hover:border-red-500" : "border-emerald-500/50 hover:border-emerald-500 bg-emerald-500/5"} backdrop-blur-sm rounded-lg p-6 border   transition-all duration-300 group transform animate-fadeIn">
    
    <div class="flex items-center justify-between pb-6 border-b border-primary-700/30">
        <div class="flex items-center space-x-4">
            <div class="bg-secondary-500/10 p-3 rounded-lg">
                <svg class="w-5 h-5 text-white">
                    <use xlink:href="/static/assets/svg/sprite17.svg#${ticket.product.name.toLowerCase()}Icon"></use>
                </svg>
            </div>
            <div>
                <div class="text-lg font-semibold text-white">
                    <span class=" text-primary-100 capitalize">${ticket.product.name.toLowerCase()}</span>
                </div>
            </div>
        </div>
        <div class="text-right">
            <div class="text-sm text-primary-300">Total Odds</div>
            <div class="text-xl font-bold text-secondary-400">${ticket.total_odds.toFixed(2)}</div>
        </div>
    </div>
    
    <div class="relative mt-6">
        
    
  `;

  // loop over ticket.bet_lines
  ticket.bet_lines.forEach((bet_line, index) => {
    html += `
    <div class="relative betLines betLines--${bet_line.status.toLowerCase()} ${index + 1 == ticket.bet_lines.length ? "before:bg-transparent" : ""}">
            <div class="flex items-start space-x-4 py-3">
                <div class="relative z-10">
    
                    <div class="w-8 h-8 rounded-full flex items-center justify-center ">
                        <svg class="w-6 h-6 betStatusIcon ${bet_line.status == "WON" ? "text-green-500" : "text-red-500"}">
                            <use xlink:href="/static/assets/svg/sprite17.svg#${bet_line.status.toLowerCase()}BetIcon"></use>
                        </svg>
                    </div>
                </div>
                <div class="flex items-top flex-col w-full">
                    <div class="flex items-center justify-between gap-4 pb-4">
                        <div>
                            <div class="text-primary-100 font-bold break-words text-lg">${bet_line.bet}</div>
                            <div class="text-primary-200 text-sm font-medium break-words">${bet_line.bet_type}</div>
                        </div>
                        <div class="flex items-center">
                            <div class="px-2 py-1 rounded-lg bg-secondary-500/10 text-secondary-400 text-sm font-medium">${
                              bet_line.odds
                            }
                            </div>
                        </div>
                    </div>
                    <div class="p-4 rounded-lg bg-[#0D151E]/50 flex items-center justify-between gap-2">
    
                        <div class="flex flex-col items-start justify-start gap-2 w-full">
                            <div class="flex justify-between items-center w-full">
                                <div class="flex items-center justify-start gap-4">
                                    <img src="${bet_line.match.home_team.logo}" class="h-4 w-auto">
                                    <p class="text-primary-300 text-sm break-words text-left">${
                                      bet_line.match.home_team.name
                                    }</p>
                                </div>
                                <p class="text-xs text-end p-1 rounded-lg bg-secondary-500/10 text-primary-200">${
                                  bet_line.match.home_team_score
                                }
                            </div>
    
                            <div class="flex justify-between items-center w-full">
                                <div class="flex items-center justify-start gap-4">
                                    <img src="${bet_line.match.away_team.logo}" class="h-4 w-auto">
                                    <p class="text-primary-300 text-sm break-words  text-left">${
                                      bet_line.match.away_team.name
                                    }</p>
                                </div>
                                <p class="text-xs text-end p-1 rounded-lg bg-secondary-500/10 text-primary-200">${
                                  bet_line.match.away_team_score
                                }</p>
                            </div>
                        </div>
    
                    </div>
                </div>
            </div>
        </div>`;
  });

  html += "<div>";
  return html;
}

function createSoloPickHtml(prediction) {
  return `
    <div class="
     ${prediction.status == "LOST" ? "bg-red-500/10 border-red-500/50 hover:border-red-500" : "bg-[#14212e] border-emerald-500/50 hover:border-emerald-500"}
            backdrop-blur-sm rounded-lg p-6 border   transition-all duration-300 group transform animate-fadeIn">
        <div class="mb-6">
    
            <div class="flex  justify-center items-center space-x-3 text-primary-300">
                <div class="bg-primary-900/80 p-2 rounded-lg">
                    <svg class="w-5 h-5 text-white"><use xlink:href="/static/assets/svg/sprite17.svg#${prediction.match.type.toLowerCase()}Icon"></use></svg>
                </div>
                <span class=" text-primary-100 capitalize">${prediction.match.type.toLowerCase()}</span> 
            </div>
   
        </div>
    
        <div class="mb-6">
            <div class="flex items-center justify-center mb-2">
                ${prediction.status == "LOST" ? '<div class="flex items-center justify-end gap-2"><p class="text-red-500 font-bold">LOST</p><svg class="w-5 h-5 text-red-500"><use xlink:href="/static/assets/svg/sprite17.svg#circleX"></use></svg> </div>' : '<div class="flex items-center justify-end gap-2"><p class="text-emerald-500 font-bold">WON</p><svg class="w-5 h-5 text-emerald-500"><use xlink:href="/static/assets/svg/sprite17.svg#circleCheck"></use></svg></div>'}
            </div>
            <div class="bg-[#0D151E] border-primary-700/50 rounded-lg border p-4 shadow-lg relative group-hover:border-secondary-500/30 transition-all duration-300 flex flex-col gap-4">
                <div class="w-full flex items-center justify-center gap-2 relative pb-4">
    
                    <img src="${prediction.match.league.country.logo}" alt="" width="20"
                         style="height: auto!important">
                    <p class="text-emerald-500 font-bold">${prediction.match.league.name}</p>
                    <div class="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-secondary-500/50 to-transparent"></div>
                </div>
    
                <div class="flex items-center justify-center gap-1">
                    <p class="text-primary-200 text-xs">Date, Time</p>
                <p class="text-white text-xs dateItem">${formatIsoString(prediction.match.kickoff_datetime)}</p>

                </div>
    
                <div class=" grid grid-cols-3 ">
                    <div class="flex flex-col items-center justify-center gap-2">
                        <img src="${prediction.match.home_team.logo}" class="h-8 lg:h-12 w-auto">
                        <p class="text-primary-100 text-sm md:text-base font-bold text-center">${
                          prediction.match.home_team.name
                        }</p>
                    </div>
                    <div class="flex items-center justify-center relative">
    
                        <p class="font-bold text-primary-200 absolute ${prediction.match.type == "SOCCER" ? "left-3" : "left-0"} md:left-0  text-sm">
                            ${prediction.match.home_team_score}</p>
                        <img src="/static/assets/images/vs.png" alt=""
                             class="w-4 md:w-8 h-auto">
                        <p class="font-bold text-primary-200 absolute ${prediction.match.type == "SOCCER" ? "right-3" : "right-0"} md:right-0  text-sm">
                            ${prediction.match.away_team_score}</p>
                    </div> 
    
                    <div class="flex flex-col items-center justify-center gap-2">
                        <img src="${prediction.match.away_team.logo}" class="h-8 lg:h-12 w-auto">
                        <p class="text-primary-100 text-sm md:text-base font-bold text-center">${
                          prediction.match.away_team.name
                        }</p>
                    </div>
                </div>
    
                <div class="relative">
                    <div class="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-secondary-500/50 to-transparent"></div>
                </div>
                <div class="flex items-center justify-center gap-1">
                    <svg class="w-5 h-5 text-emerald-400"><use xlink:href="/static/assets/svg/sprite17.svg#chevronUp"></use></svg>
    
                    <p class="text-primary-100">Odds</p>
                    <span class="text-emerald-400 font-bold">${prediction.odds}</span>
                </div>
    
            </div>
        </div>
    
        <div class="flex flex-col items-center justify-center">
            <div class="text-sm text-white">Prediction</div>
            <div class="font-semibold text-xl text-center  ${prediction.status == "LOST" ? "text-red-500" : "text-emerald-500"}">
                ${prediction.prediction}
            </div>
        </div>
    
    
    </div>

  `;
}

function getQueryUrl() {
  let url = loadMoreButton.dataset.queryUrl;

  if (url.includes("?")) {
    url += `&page=${currentPage}&page_size=20`;
  } else {
    url += `?page=${currentPage}&page_size=20`;
  }

  console.log(`getQueryUrl: ${url}`);
  return url;
}

async function fetchPredictions() {
  const url = getQueryUrl();

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("An unexpected error has occured. Please try again.");
    }
    const data = await response.json();

    hasNext = data.next !== null;

    if (hasNext) {
      currentPage++;
    }

    predictions = data.results;
  } catch (error) {
    console.error(error);
    loadMoreButton.disabled = true;
    loadMoreButton.classList.add("hidden");
    hasNext = false;
  }
}

export { initLoadMorePredictionsButton };
