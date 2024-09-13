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
});
