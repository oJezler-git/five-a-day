document.addEventListener('DOMContentLoaded', function () {

    var animationLeft = bodymovin.loadAnimation({

        container: document.getElementById('lottie-background-left'),

        renderer: 'svg',

        loop: true,

        autoplay: true,

        path: 'https://uploads-ssl.webflow.com/63c6b6a8e34f347803dc4c5a/63c72e591d68c14a86db2727_night-sky.json',

        rendererSettings: {

            preserveAspectRatio: 'xMidYMid slice'

        }

    });



    var animationRight = bodymovin.loadAnimation({

        container: document.getElementById('lottie-background-right'),

        renderer: 'svg',

        loop: true,

        autoplay: true,

        path: 'https://uploads-ssl.webflow.com/63c6b6a8e34f347803dc4c5a/63c72e591d68c14a86db2727_night-sky.json',

        rendererSettings: {

            preserveAspectRatio: 'xMidYMid slice'

        }

    });



    animationLeft.setSpeed(0.5); // speed

    animationRight.setSpeed(0.5);





    // var overlayLeft = document.createElement('div');

    // overlayLeft.className = 'lottie-overlay';

    // document.getElementById('lottie-background-left').appendChild(overlayLeft);

    //

    // var overlayRight = document.createElement('div');

    // overlayRight.className = 'lottie-overlay';

    // document.getElementById('lottie-background-right').appendChild(overlayRight);

    const numSymbol = 25;
    const symbolArray = [];
    const svg = document.getElementById('symbol-container');

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;

    document.addEventListener('mousemove', (event) => {
        mouseX = event.clientX;
        mouseY = event.clientY;
    });

    const symbols = ['×', '+', '-', '÷'];

    for (let i = 0; i < numSymbol; i++) {
        const symbol = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        symbol.setAttribute('fill', 'lightblue');
        symbol.setAttribute('font-size', '20');
        symbol.setAttribute('text-anchor', 'middle');
        symbol.setAttribute('dominant-baseline', 'middle');
        symbol.textContent = symbols[Math.floor(Math.random() * symbols.length)];
        symbol.style.filter = 'drop-shadow(0 0 10px rgba(0, 255, 255, 0.8))';
        svg.appendChild(symbol);
        
        symbolArray.push({
            element: symbol,
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            speedX: Math.random() * 2 + 0.5,
            speedY: Math.random() * 2 + 0.5,
            sway: Math.random() * 0.02 - 0.01,
            direction: Math.random() * Math.PI * 2,
        });
    }

    function animateSymbol() {
        symbolArray.forEach(symbol => {
            symbol.x += symbol.speedX * Math.cos(symbol.direction);
            symbol.y += symbol.speedY * Math.sin(symbol.direction);
            symbol.x += Math.sin(symbol.direction) * symbol.sway * 30;
            symbol.y += Math.cos(symbol.direction) * symbol.sway * 20;
            symbol.direction += symbol.sway;
            
            if (symbol.x > window.innerWidth || symbol.x < 0) {
                symbol.speedX = -symbol.speedX;
            }
            if (symbol.y > window.innerHeight || symbol.y < 0) {
                symbol.speedY = -symbol.speedY;
            }
            
            symbol.x += (mouseX - symbol.x) * 0.01;
            symbol.y += (mouseY - symbol.y) * 0.01;
            
            symbol.element.setAttribute('x', symbol.x);
            symbol.element.setAttribute('y', symbol.y);
        });
        requestAnimationFrame(animateSymbol);
    }

    animateSymbol();


});


