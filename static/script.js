document.addEventListener("DOMContentLoaded", function () {
    const board = document.getElementById("board");
    const undoButton = document.getElementById("undo-btn");
    const passButton = document.getElementById("pass-btn");
    const resetButton = document.getElementById("reset-btn");

    undoButton.addEventListener("click", undoMove);  // 1手戻すボタン
    passButton.addEventListener("click", passTurn);  // パスボタン
    resetButton.addEventListener("click", resetGame);

    resetGame();

    // 盤面を生成する関数
    function createBoard(boardData = null) {
        board.innerHTML = "";
        for (let y = 0; y < 10; y++) {
            for (let x = 0; x < 10; x++) {
                const cell = document.createElement("div");
                cell.classList.add("cell");
                cell.dataset.x = x;
                cell.dataset.y = y;
                if (boardData && boardData[y][x] === "R") {
                    const redStone = document.createElement("div");
                    redStone.classList.add("stone", "red-stone");
                    cell.appendChild(redStone);
                } else if (boardData && boardData[y][x] === "B") {
                    const blueStone = document.createElement("div");
                    blueStone.classList.add("stone", "blue-stone");
                    cell.appendChild(blueStone);
                }
                cell.addEventListener("click", makeMove);
                board.appendChild(cell);
            }
        }
    }
    // ゲームをリセットする関数
    function resetGame() {
        createBoard();  // ゲームをやり直すために盤面をリセット

    }

    // ボードを更新する関数
    function updateBoard(data) {
        const cells = document.querySelectorAll(".cell");
        cells.forEach(cell => {
            const x = parseInt(cell.dataset.x);
            const y = parseInt(cell.dataset.y);
            const piece = data.board[x][y];
            cell.innerHTML = "";
            if (piece === "R") {
                const redStone = document.createElement("div");
                redStone.classList.add("stone", "red-stone");
                cell.appendChild(redStone);
            } else if (piece === "B") {
                const blueStone = document.createElement("div");
                blueStone.classList.add("stone", "blue-stone");
                cell.appendChild(blueStone);
            }

        });

        // 取った駒の数を表示
        document.getElementById("captured-red").textContent = data.captured_red;
        document.getElementById("captured-blue").textContent = data.captured_blue;


        // 駒が描画された後でゲーム終了判定
        if (data.result) {
            setTimeout(() => {
                document.getElementById("game-result").style.display = "block";
                document.getElementById("result-text").textContent = data.result;
            }, 300);  // 少し遅延を入れて駒が描画されてから結果を表示
        }
    }

    // 駒を置く処理
    function makeMove(event) {
        const x = parseInt(event.target.dataset.x);
        const y = parseInt(event.target.dataset.y);
        console.log(`Clicked: x=${x}, y=${y}`);
        if (isNaN(x) || isNaN(y)) {
            alert("無効な座標が選択されました！");
            return;
        }
        fetch("/move", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ x: x, y: y })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateBoard(data);
            } else {
                const emptyCells = document.querySelectorAll(".cell").length - document.querySelectorAll(".cell div").length;
                if (emptyCells > 1) {
                    alert("このマスには駒を置けません！");
                }
            }
        });
    }

    // 1手戻す処理
    function undoMove() {
        fetch("/undo", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            updateBoard(data);
            // 取った駒の数を更新
            document.getElementById("captured-red").textContent = data.captured_red;
            document.getElementById("captured-blue").textContent = data.captured_blue;

            // アラートを表示
            alert("1手戻されました");
        });

    }

    // パスする処理
    function passTurn() {
        fetch("/pass", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            // 現在のターンを正しく表示する
            alert("手番をパスしました");
            updateBoard(data);  // パス後にターン表示を更新
        });
    }

    // ゲームをリセットする処理
    function resetGame() {
    　　fetch("/reset", { method: "POST" })
        .then(response => response.json())
        .then(data => {
        　 createBoard();  // ゲームを最初からやり直す
           document.getElementById("captured-red").textContent = data.captured_red;
           document.getElementById("captured-blue").textContent = data.captured_blue;
           alert("ゲームをリセットしました");
        });
    }

    createBoard();
});

