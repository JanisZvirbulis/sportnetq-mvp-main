
// CANVAS

const canvas = document.getElementById("drawing-canvas");
const ctx = canvas.getContext("2d");

let drawing = false;

canvas.addEventListener("mousedown", startDrawing);
canvas.addEventListener("mousemove", draw);
canvas.addEventListener("mouseup", stopDrawing);
canvas.addEventListener("mouseout", stopDrawing);

function startDrawing(event) {
    drawing = true;
    ctx.beginPath();
    ctx.moveTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
}

function draw(event) {
    if (!drawing) return;
    ctx.lineTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
    ctx.stroke();
}

function stopDrawing() {
    drawing = false;
    ctx.beginPath(); // Start a new path when stopping drawing
}

function setBackground(src) {
    const img = new Image();
    img.src = src;
    img.onload = function () {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
}

document.getElementById("background-image").addEventListener("change", function (event) {
    setBackground(event.target.value);
});

document.getElementById("save-btn").addEventListener("click", function () {
    const link = document.createElement("a");
    link.href = canvas.toDataURL();
    link.download = "canvas_image.png";
    link.click();
});

// undo & redo
let history = [];
let historyIndex = -1;

function updateHistory() {
    const newSnapshot = canvas.toDataURL();
    history = history.slice(0, historyIndex + 1);
    history.push(newSnapshot);
    historyIndex++;
}

function undo() {
    if (historyIndex <= 0) return;
    historyIndex--;
    const img = new Image();
    img.src = history[historyIndex];
    img.onload = function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
}

function redo() {
    if (historyIndex >= history.length - 1) return;
    historyIndex++;
    const img = new Image();
    img.src = history[historyIndex];
    img.onload = function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
}

canvas.addEventListener("mousedown", (event) => {
    updateHistory();
    startDrawing(event);
});

document.getElementById("undo-btn").addEventListener("click", undo);
document.getElementById("redo-btn").addEventListener("click", redo);

// Brush color
const brushColorButtons = document.querySelectorAll(".brush-colors button");

function changeBrushColor(event) {
  ctx.strokeStyle = event.target.value;
}

brushColorButtons.forEach(button => {
  button.addEventListener("click", changeBrushColor);
});

// Brush size
const brushSizeButtons = document.querySelectorAll(".brushes button");

function changeBrushSize(event) {
  ctx.lineWidth = parseInt(event.target.value);
}

brushSizeButtons.forEach(button => {
  button.addEventListener("click", changeBrushSize);
});


function startDrawing(event) {
    drawing = true;
    ctx.lineWidth = getBrushSize(); // Set the brush size before starting to draw
    ctx.beginPath();
    ctx.moveTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
}

// Set default background
const defaultBackground = document.getElementById("background-image").value;
setBackground(defaultBackground);
updateHistory();

// Set default brush size
document.querySelector(".brushes button[value='3']").click();

// window.onload = function () {

//     // Definitions
//     var canvas = document.getElementById("paint-canvas");
//     var context = canvas.getContext("2d");
//     var boundings = canvas.getBoundingClientRect();
  
//     // Specifications
//     var mouseX = 0;
//     var mouseY = 0;
//     context.strokeStyle = 'black'; // initial brush color
//     context.lineWidth = 1; // initial brush width
//     var isDrawing = false;
  
  
//     // Handle Colors
//     var colors = document.getElementsByClassName('colors')[0];
  
//     colors.addEventListener('click', function(event) {
//       context.strokeStyle = event.target.value || 'black';
//     });
  
//     // Handle Brushes
//     var brushes = document.getElementsByClassName('brushes')[0];
  
//     brushes.addEventListener('click', function(event) {
//       context.lineWidth = event.target.value || 1;
//     });
  
//     // Mouse Down Event
//     canvas.addEventListener('mousedown', function(event) {
//       setMouseCoordinates(event);
//       isDrawing = true;
  
//       // Start Drawing
//       context.beginPath();
//       context.moveTo(mouseX, mouseY);
//     });
  
//     // Mouse Move Event
//     canvas.addEventListener('mousemove', function(event) {
//       setMouseCoordinates(event);
  
//       if(isDrawing){
//         context.lineTo(mouseX, mouseY);
//         context.stroke();
//       }
//     });
  
//     // Mouse Up Event
//     canvas.addEventListener('mouseup', function(event) {
//       setMouseCoordinates(event);
//       isDrawing = false;
//     });
  
//     // Handle Mouse Coordinates
//     function setMouseCoordinates(event) {
//       mouseX = event.clientX - boundings.left;
//       mouseY = event.clientY - boundings.top;
//     }
  
//     // Handle Clear Button
//     var clearButton = document.getElementById('clear');
  
//     clearButton.addEventListener('click', function() {
//       context.clearRect(0, 0, canvas.width, canvas.height);
//     });
  
//     // Handle Save Button
//     var saveButton = document.getElementById('save');
  
//     saveButton.addEventListener('click', function() {
//       var imageName = prompt('Please enter image name');
//       var canvasDataURL = canvas.toDataURL();
//       var a = document.createElement('a');
//       a.href = canvasDataURL;
//       a.download = imageName || 'drawing';
//       a.click();
//     });
//   };
// const canvas = document.getElementById("drawing-canvas");
// const ctx = canvas.getContext("2d");

// let drawing = false;

// canvas.addEventListener("mousedown", startDrawing);
// canvas.addEventListener("mousemove", draw);
// canvas.addEventListener("mouseup", stopDrawing);
// canvas.addEventListener("mouseout", stopDrawing);

// // function startDrawing(event) {
// //     drawing = true;
// //     ctx.beginPath();
// //     ctx.moveTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
// // }

// function draw(event) {
//     if (!drawing) return;
//     ctx.lineTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
//     ctx.stroke();
// }

// function stopDrawing() {
//     drawing = false;
// }

// function setBackground(src) {
//     const img = new Image();
//     img.src = src;
//     img.onload = function () {
//         ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
//         updateCanvas();
//         updateHistory();
//     };
// }

// document.getElementById("background-image").addEventListener("change", function (event) {
//     setBackground(event.target.value);
// });

// document.getElementById("save-btn").addEventListener("click", function () {
//     const link = document.createElement("a");
//     link.href = canvas.toDataURL();
//     link.download = "canvas_image.png";
//     link.click();
// });

// // undo & redo
// let history = [];
// let historyIndex = -1;

// function updateHistory() {
//     const newSnapshot = canvas.toDataURL();
//     history = history.slice(0, historyIndex + 1);
//     history.push(newSnapshot);
//     historyIndex++;
// }

// function undo() {
//     if (historyIndex <= 0) return;
//     historyIndex--;
//     const img = new Image();
//     img.src = history[historyIndex];
//     img.onload = function () {
//         ctx.clearRect(0, 0, canvas.width, canvas.height);
//         ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
//         updateCanvas();
//     };
// }

// function redo() {
//     if (historyIndex >= history.length - 1) return;
//     historyIndex++;
//     const img = new Image();
//     img.src = history[historyIndex];
//     img.onload = function () {
//         ctx.clearRect(0, 0, canvas.width, canvas.height);
//         ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
//         updateCanvas();
//     };
// }

// canvas.addEventListener("mousedown", (event) => {
//     updateHistory();
//     startDrawing(event);
// });

// document.getElementById("undo-btn").addEventListener("click", undo);
// document.getElementById("redo-btn").addEventListener("click", redo);

// // Brush size
// const brushSizeInput = document.getElementById("brush-size");

// function getBrushSize() {
//     return parseInt(brushSizeInput.value);
// }

// function startDrawing(event) {
//     drawing = true;
//     ctx.lineWidth = getBrushSize(); // Set the brush size before starting to draw
//     ctx.beginPath();
//     ctx.moveTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
// }


//   // Set default background
//   const defaultBackground = document.getElementById("background-image").value;
//   setBackground(defaultBackground);

//   // Add a variable to store the current mode
// let mode = "draw";

// // Modify event listeners to handle the mode
// canvas.addEventListener("mousedown", (event) => {
//     if (mode === "draw") {
//         updateHistory();
//         startDrawing(event);
//     } else if (mode === "rectangle") {
//         startRectangle(event);
//     }
// });

// // Modify the startDrawing function to handle different modes
// function startDrawing(event) {
//     if (mode !== "draw") return;

//     drawing = true;
//     ctx.lineWidth = getBrushSize(); // Set the brush size before starting to draw
//     ctx.beginPath();
//     ctx.moveTo(event.clientX - canvas.offsetLeft, event.clientY - canvas.offsetTop);
// }

// // Add a new function for drawing a rectangle
// function startRectangle(event) {
//     if (mode !== "rectangle") return;

//     updateHistory();
//     const x = event.clientX - canvas.offsetLeft;
//     const y = event.clientY - canvas.offsetTop;
//     const width = getBrushSize();
//     const height = getBrushSize();
//     ctx.fillRect(x, y, width, height);
// }

// // Add event listeners to change the mode
// document.getElementById("draw-mode").addEventListener("click", () => {
//     mode = "draw";
// });

// document.getElementById("rectangle-mode").addEventListener("click", () => {
//     mode = "rectangle";
// });

// class DraggableElement {
//   constructor(x, y) {
//       this.x = x;
//       this.y = y;
//       this.width = 0;
//       this.height = 0;
//       this.selected = false;
//       this.resizing = false;
//   }

//   contains(x, y) {
//       return (
//           x >= this.x &&
//           x <= this.x + this.width &&
//           y >= this.y &&
//           y <= this.y + this.height
//       );
//   }

//   move(dx, dy) {
//       this.x += dx;
//       this.y += dy;
//   }

//   resize(dx, dy) {
//       this.width += dx;
//       this.height += dy;
//   }

//   draw(ctx) {
//       // This method should be implemented by subclasses
//   }
// }

// class Arrow extends DraggableElement {
//   constructor(x, y) {
//       super(x, y);
//       this.width = 50;
//       this.height = 50;
//   }

//   draw(ctx) {
//       ctx.save();
//       ctx.translate(this.x, this.y);

//       ctx.beginPath();
//       ctx.moveTo(0, this.height / 2);
//       ctx.lineTo(this.width - 10, this.height / 2);
//       ctx.stroke();

//       ctx.beginPath();
//       ctx.moveTo(this.width, this.height / 2);
//       ctx.lineTo(this.width - 10, this.height / 4);
//       ctx.lineTo(this.width - 10, this.height * 3 / 4);
//       ctx.closePath();
//       ctx.fill();

//       ctx.restore();
//   }
// }

// class Rectangle extends DraggableElement {
//   constructor(x, y) {
//       super(x, y);
//       this.width = 50;
//       this.height = 50;
//   }

//   draw(ctx) {
//       ctx.strokeRect(this.x, this.y, this.width, this.height);
//   }
// }

// let elements = [];
// let selectedElement = null;
// let elementType = "";

// document.getElementById("element-selection").addEventListener("change", function (event) {
//     elementType = event.target.value;
//   });
  
//   canvas.addEventListener("mousedown", (event) => {
//     const x = event.clientX - canvas.offsetLeft;
//     const y = event.clientY - canvas.offsetTop;
  
//     if (elementType) {
//         let newElement;
  
//         if (elementType === "arrow") {
//             newElement = new Arrow(x, y);
//         } else if (elementType === "rectangle") {
//             newElement = new Rectangle(x, y);
//         }
  
//         if (newElement) {
//             elements.push(newElement);
//             newElement.selected = true;
//             if (selectedElement && selectedElement !== newElement) {
//                 selectedElement.selected = false;
//             }
//             selectedElement = newElement;
//             elementType = "";
//             document.getElementById("element-selection").value = "";
//             updateCanvas();
//         }
//     } else {
//         let clickedElement = null;
//         for (let i = elements.length - 1; i >= 0; i--) {
//             if (elements[i].contains(x, y)) {
//               clickedElement = elements[i];
//               break;
//           }
//       }
  
//       if (clickedElement) {
//           clickedElement.selected = true;
//           if (selectedElement && selectedElement !== clickedElement) {
//               selectedElement.selected = false;
//           }
//           selectedElement = clickedElement;
//       } else {
//           if (selectedElement) {
//               selectedElement.selected = false;
//               selectedElement = null;
//           }
//       }
//       updateCanvas();
//     }
//   });
  
//   canvas.addEventListener("mousemove", (event) => {
//       if (selectedElement && selectedElement.selected) {
//           const dx = event.movementX;
//           const dy = event.movementY;
//           selectedElement.move(dx, dy);
//           updateCanvas();
//       }
//   });
  
//   function updateCanvas() {
//       ctx.clearRect(0, 0, canvas.width, canvas.height);
//       setBackground(defaultBackground);
  
//       for (const element of elements) {
//           element.draw(ctx);
//       }
//   }
  
  // Set default background
//   const defaultBackground = document.getElementById("background-image").value;
//   setBackground(defaultBackground);