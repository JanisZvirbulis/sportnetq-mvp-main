
// lang dropdown
const dropdowns = document.querySelectorAll(".dropdown");

dropdowns.forEach((dropdown) => {
  const select = dropdown.querySelector(".select");
  const caret = dropdown.querySelector(".caret");
  const menu = dropdown.querySelector(".menu");
  const options = dropdown.querySelectorAll(".menu li");
  const selected = dropdown.querySelector(".selected");

  select.addEventListener("click", (event) => {
    event.stopPropagation(); // Prevent the event from bubbling up to the document
    select.classList.toggle("select-clicked");
    caret.classList.toggle("caret-rotate");
    menu.classList.toggle("menu-open");
  });

  options.forEach((option) => {
    option.addEventListener("click", (event) => {
      event.stopPropagation(); // Prevent the event from bubbling up to the document
      selected.innerText = option.innerText;
      select.classList.remove("select-clicked");
      caret.classList.remove("caret-rotate");
      menu.classList.remove("menu-open");
      options.forEach((option) => {
        option.classList.remove("active");
      });
      option.classList.add("active");
    });
  });
});

// Close the dropdown when clicking outside of it
document.addEventListener("click", () => {
  dropdowns.forEach((dropdown) => {
    const select = dropdown.querySelector(".select");
    const caret = dropdown.querySelector(".caret");
    const menu = dropdown.querySelector(".menu");
    select.classList.remove("select-clicked");
    caret.classList.remove("caret-rotate");
    menu.classList.remove("menu-open");
  });
});


// Back to top BUTTON
let btnForTop = document.createElement("button");
btnForTop.setAttribute("id", "btnTop");
let btnIcon =
  '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-arrow-up-circle-fill" viewBox="0 0 16 16">' +
  '<path d="M16 8A8 8 0 1 0 0 8a8 8 0 0 0 16 0zm-7.5 3.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707V11.5z"/>' +
  "  </svg>";

btnForTop.innerHTML = btnIcon;
document.body.appendChild(btnForTop); // Add to DOM

btnForTop.addEventListener("click", function () {
  window.scrollTo(0, 0);
});

// Back to top function
window.onscroll = function () {
  scrollFunction();
};

function scrollFunction() {
  if (document.body.scrollTop > 40 || document.documentElement.scrollTop > 40) {
    btnForTop.style.visibility = "visible";
    btnForTop.style.opacity = "1";
  } else {
    btnForTop.style.visibility = "hidden";
    btnForTop.style.opacity = "0";
  }
}

// Close Django messages when the close button is clicked
document.addEventListener('DOMContentLoaded', function() {
  var messages = document.querySelectorAll('.messages li');
  for (var i = 0; i < messages.length; i++) {
    var message = messages[i];
    var closeButton = document.createElement('span');
    closeButton.innerHTML = '&times;';
    closeButton.classList.add('close-button');
    message.appendChild(closeButton);
    closeButton.addEventListener('click', function() {
      this.parentElement.style.opacity = '0';
      setTimeout(function() {
        this.parentElement.style.display = 'none';
      }.bind(this), 300);
    });
    
    // Automatically close Django messages after 10 seconds
    if (!message.classList.contains('extra')) {
      setTimeout(function(msg) {
        msg.style.opacity = '0';
        setTimeout(function() {
          msg.style.display = 'none';
        }, 300);
      }, 10000, message);
    }
  }
});

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('.analytics-score-table').forEach(table => {
      let bestScoreLower = table.dataset.bestScoreLower === 'True';
      let assessmentType = table.dataset.scoreType;
      let epsilon = 1e-6;  // Adjust this line
      console.log('assessmentType', assessmentType)
      let scores = [];
      let rows = table.getElementsByTagName('tr');
  

      for (let i = 1; i < rows.length; i++) {
          let scoreCell = rows[i].getElementsByTagName('td')[1];
          let scoreText = scoreCell.innerText.trim();

          // Determine the assessment type
          
          if (assessmentType === 'time') {
              score = isTimeFormat(scoreText) ? convertTimeToMilliseconds(scoreText) : parseFloat(scoreText);
          } else if (assessmentType === 'result') {
              score = parseFloat(scoreText);
          } else if (assessmentType === 'distance') {
              console.log('scoreText', scoreText)
              // Parse the distance using the same formatting logic as in Django template filter
              score = parseDistance(scoreText);
          } else {
              score = parseFloat(scoreText); // Default to parsing as a number
          }

          scores.push({ score: score, row: i });
      }

      // Sort scores based on the assessment type
      scores.sort((a, b) => {
          if (bestScoreLower) {
              return a.score - b.score;
          } else {
              return b.score - a.score;
          }
      });

      if (scores.length > 0) {
          let bestValue = scores[0].score;

          // Highlight all the scores equal to the best value within the threshold
          scores.forEach(scoreInfo => {
              if (Math.abs(scoreInfo.score - bestValue) < epsilon) {
                  rows[scoreInfo.row].getElementsByTagName('td')[1].style.backgroundColor = 'grey';
              }
          });
      }
  });
});

function parseDistance(distanceString) {
  // Regular expression to match numerical values and units (e.g., "3 m 99 cm")
  const regex = /(\d+(\.\d+)?)\s*(m|cm|mm|km)?/g;
  console.log(distanceString)
  let match;
  let distance = 0;

  while ((match = regex.exec(distanceString)) !== null) {
      const value = parseFloat(match[1]);
      const unit = match[3];

      if (!isNaN(value) && unit) {
          switch (unit) {
              case 'km':
                  distance += value * 1000;
                  break;
              case 'm':
                  distance += value;
                  break;
              case 'cm':
                  distance += value / 100;
                  break;
              case 'mm':
                  distance += value / 1000;
                  break;
              default:
                  // Invalid unit
                  return -1;
          }
      }
  }

  return distance;
}

function isTimeFormat(text) {
  return /^(\d+h\s)?(\d+m\s)?(\d+(\.\d{1,3})?s)?$/.test(text);
}

function convertTimeToMilliseconds(timeString) {
  let totalMilliseconds = 0;

  let hoursMatch = timeString.match(/(\d+)h/);
  if (hoursMatch) {
      totalMilliseconds += parseInt(hoursMatch[1]) * 60 * 60 * 1000;
  }

  let minutesMatch = timeString.match(/(\d+)m/);
  if (minutesMatch) {
      totalMilliseconds += parseInt(minutesMatch[1]) * 60 * 1000;
  }

  let secondsMatch = timeString.match(/(\d+(\.\d{1,3})?)s/);
  if (secondsMatch) {
      totalMilliseconds += parseFloat(secondsMatch[1]) * 1000;
  }

  return totalMilliseconds;
}



// document.addEventListener("DOMContentLoaded", function () {
//   document.querySelectorAll('.analytics-score-table').forEach(table => {
//       let bestScoreLower = table.dataset.bestScoreLower === 'True';
//       let epsilon = 1e-6;  // Adjust this line

//       let scores = [];
//       let rows = table.getElementsByTagName('tr');

//       for (let i = 1; i < rows.length; i++) {
//           let scoreCell = rows[i].getElementsByTagName('td')[1];
//           let scoreText = scoreCell.innerText.trim();
//           let score = isTimeFormat(scoreText) ? convertTimeToMilliseconds(scoreText) : parseFloat(scoreText);
//           scores.push({score: score, row: i});
//       }

//       scores.sort((a, b) => bestScoreLower ? a.score - b.score : b.score - a.score);

//       if (scores.length > 0) {
//           let bestValue = scores[0].score;

//           // Highlight all the scores equal to the best value within the threshold
//           scores.forEach(scoreInfo => {
//               if (Math.abs(scoreInfo.score - bestValue) < epsilon) {  // Modify this line
//                   rows[scoreInfo.row].getElementsByTagName('td')[1].style.backgroundColor = 'grey';
//               }
//           });
//       }
//   });
// });

