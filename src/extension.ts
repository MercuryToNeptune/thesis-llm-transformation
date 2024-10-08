import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
	// Register the command to open the WebView
	const command = vscode.commands.registerCommand('extension.showHelloWorldWebview', () => {
		const panel = vscode.window.createWebviewPanel(
			'helloWorld', // Identifies the type of the webview. Used internally
			'Transformation Tool', // Title of the panel displayed to the user
			vscode.ViewColumn.One, // Editor column to show the new webview panel in.
			{
				enableScripts: true, // Enables JavaScript within the webview
			}
		);

		// Set the webview's HTML content
		panel.webview.html = getWebviewContent();

		// Handle messages from the webview
		panel.webview.onDidReceiveMessage(
			(message) => {
				switch (message.command) {
					case 'runPython':
						runPythonScript(panel);
						break;
				}
			},
			undefined,
			context.subscriptions
		);
	});

	context.subscriptions.push(command);
}

// Function to execute the Python script and send real-time output back to the webview
function runPythonScript(panel: vscode.WebviewPanel) {
	const workspaceFolders = vscode.workspace.workspaceFolders;
	if (workspaceFolders) {
		const workspacePath = workspaceFolders[0].uri.fsPath;

		// Adjust the path to point to '../main.py' relative to the workspace folder
		const pythonFilePath = path.join(workspacePath, 'main.py');

		// Wrap the path in quotes to handle spaces or special characters
		const quotedPythonFilePath = `"${pythonFilePath}"`;

		// Spawn the Python process with the `-u` flag for unbuffered output, setting the cwd to the parent directory
		const pythonProcess = cp.spawn('python3', ['-u', quotedPythonFilePath], { cwd: workspacePath, shell: true });

		// Listen to stdout (real-time logs)
		pythonProcess.stdout.on('data', (data) => {
			panel.webview.postMessage({ command: 'showLogs', logs: data.toString() });
		});

		// Listen to stderr (error logs)
		pythonProcess.stderr.on('data', (data) => {
			panel.webview.postMessage({ command: 'showLogs', logs: `Error: ${data.toString()}` });
		});

		// Handle the close event (when Python script finishes execution)
		pythonProcess.on('close', (code) => {
			if (code !== 0) { // Only show the exit code if it's non-zero (indicating an error)
				panel.webview.postMessage({ command: 'showLogs', logs: `Process exited with code ${code}` });
			}
		});
	} else {
		panel.webview.postMessage({ command: 'showLogs', logs: 'No workspace folder found' });
	}
}


// Function to provide the HTML content of the WebView
function getWebviewContent() {
	return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Logs</title>
            <style>
                .section {
                    border: 1px solid #ccc;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                }
				/* Success border styling when the tick is displayed */
				.section-success {
					border-color: #28a745 !important; /* Bootstrap Success Green */
				}
                .section h3 {
                    cursor: pointer;
                    margin: 0;
                }
                .section-content {
                    display: none;
                    margin-top: 10px;
                }
                .section-content.active {
                    display: block;
                }
                .tick {
                    color: green;
                    font-weight: bold;
                }
                .hidden {
                    display: none !important; /* Ensure the button hides properly */
                }

				#preprocessingContent {
					white-space: pre-wrap; /* Ensure line breaks and spaces are preserved */
				}

                /* Spinner visibility handling */
                .spinner {
    				border: 3px solid rgba(0, 0, 0, 0.1);
					border-left-color: #09f;
					border-radius: 50%;
					width: 14px; /* Adjust width to match text size */
					height: 14px; /* Adjust height to match text size */
					animation: spin 1s linear infinite;
					display: inline-block;
					margin-left: 10px;
					visibility: hidden; /* Hidden by default */
					vertical-align: middle; /* Aligns spinner vertically with text */
					line-height: normal; /* Ensures spinner height matches text line height */
				}

				/* Material Design Blue Button - Now more Bootstrap-like */
				button {
					background-color: #28a745; /* Bootstrap Success Green */
					color: white;
					border: none;
					border-radius: 4px;
					padding: 10px 20px;
					font-size: 16px;
					font-weight: bold;
					cursor: pointer;
					box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
					transition: background-color 0.3s ease, box-shadow 0.3s ease;
					text-transform: uppercase;
				}

				button:hover {
					background-color: #218838; /* Darker green on hover */
				}

				button:active {
					background-color: #1e7e34; /* Even darker green on click */
					box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2);
				}

				button:focus {
					outline: none;
					box-shadow: 0px 0px 10px rgba(40, 167, 69, 0.5); /* Green shadow on focus */
				}

				/* Centering the button */
				#buttonContainer {
					display: flex;
					justify-content: center;
					align-items: center;
					height: 80vh; /* Full viewport height to vertically center */
				}

                @keyframes spin {
                    100% {
                        transform: rotate(360deg);
                    }
                }
            </style>
        </head>
        <body>
            <h1>🚀Welcome to the LLM-based Transformation Tool🚀</h1>
			<div id="logsContainer" class="hidden">
                <div class="section">
                    <h3 id="preprocessing">Pre-processing <span id="tick-preprocessing"></span><span id="preprocessing-loader" class="spinner"></span></h3>
                    <div id="preprocessingContent" class="section-content"></div>
                </div>
                <div class="section">
					<h3 id="platformBuild">Generating Platform Build File <span id="tick-platformBuild"></span><span id="platformBuild-loader" class="spinner"></span></h3>
					<div id="platformBuildContent" class="section-content"></div>
				</div>
                <div class="section">
					<h3 id="platformSource">Generating Platform Source-code <span id="tick-platformSource"></span><span id="platformSource-loader" class="spinner"></span></h3>
					<div id="platformSourceContent" class="section-content"></div>
				</div>
				<div class="section">
					<h3 id="postProcessing">Post-processing <span id="tick-postProcessing"></span><span id="postProcessing-loader" class="spinner"></span></h3>
					<div id="postProcessingContent" class="section-content"></div>
				</div>
            </div>
            <div id="buttonContainer">
                <button id="runBtn">Run app on the set of cloned variants</button>
            </div>

            

			<script>
				const vscode = acquireVsCodeApi();
				let logBuffer = ''; // Buffer to accumulate logs until "Pre-processing complete" is detected
				let isPreprocessingComplete = false; // Flag to track when pre-processing is complete
				let isPlatformBuildComplete = false; // Flag to track when platform build is complete or failed
				let isPlatformSourceComplete = false; // Flag to track when platform source-code is complete
				let isPostProcessingComplete = false;

				// Button click event
				document.getElementById('runBtn').addEventListener('click', () => {
					vscode.postMessage({ command: 'runPython' });

					// Hide the button and show the logs container
					document.getElementById('runBtn').classList.add('hidden');
					document.getElementById('logsContainer').classList.remove('hidden');

					// Show the spinner by changing its visibility for Pre-processing
					const preprocessingLoader = document.getElementById('preprocessing-loader');
					preprocessingLoader.style.visibility = 'visible';
				});

				// Toggle sections
				document.querySelectorAll('.section h3').forEach((header) => {
					header.addEventListener('click', () => {
						const content = header.nextElementSibling;
						content.classList.toggle('active');
					});
				});

				// Handle messages sent from the extension to the webview
				window.addEventListener('message', event => {
					const message = event.data;
					switch (message.command) {
						case 'showLogs':
							handleLogs(message.logs);
							break;
					}
				});

				function handleLogs(logs) {
					if (!isPreprocessingComplete) {
						// Pre-processing section handling
						const preprocessingContent = document.getElementById('preprocessingContent');
						const preprocessingSection = document.getElementById('preprocessing').parentElement;

						const logElement = document.createElement('pre');
						logElement.textContent = logs;
						preprocessingContent.appendChild(logElement);

						if (logs.includes('Pre-processing complete')) {
							document.getElementById('tick-preprocessing').textContent = '✔️';
							const preprocessingLoader = document.getElementById('preprocessing-loader');
							preprocessingLoader.style.visibility = 'hidden'; // Hide spinner
							preprocessingContent.classList.add('active');
							preprocessingSection.classList.add('section-success');
							isPreprocessingComplete = true;

							const platformBuildLoader = document.getElementById('platformBuild-loader');
							platformBuildLoader.style.visibility = 'visible'; // Show spinner for platform build
						}
					} else if (!isPlatformBuildComplete) {
						// Platform Build section handling
						const platformBuildContent = document.getElementById('platformBuildContent');
						const platformBuildSection = document.getElementById('platformBuild').parentElement;

						const logElement = document.createElement('pre');
						logElement.textContent = logs;
						platformBuildContent.appendChild(logElement);

						if (logs.includes('Generation of platform build file complete')) {
							document.getElementById('tick-platformBuild').textContent = '✔️';
							const platformBuildLoader = document.getElementById('platformBuild-loader');
							platformBuildLoader.style.visibility = 'hidden'; // Hide spinner
							platformBuildContent.classList.add('active');
							platformBuildSection.classList.add('section-success');
							isPlatformBuildComplete = true;

							// Show the spinner for platform source-code step
							const platformSourceLoader = document.getElementById('platformSource-loader');
							platformSourceLoader.style.visibility = 'visible'; // Make sure the spinner is visible for platform source
						} else if (logs.includes('Generation of platform build file not successful')) {
							document.getElementById('tick-platformBuild').textContent = '❌';
							const platformBuildLoader = document.getElementById('platformBuild-loader');
							platformBuildLoader.style.visibility = 'hidden'; // Hide spinner
							platformBuildContent.classList.add('active');
							platformBuildSection.classList.add('section-failure');
							isPlatformBuildComplete = true;
						}
					} else if (!isPlatformSourceComplete) {
						// Platform Source-code section handling
						const platformSourceContent = document.getElementById('platformSourceContent');
						const platformSourceSection = document.getElementById('platformSource').parentElement;

						const logElement = document.createElement('pre');
						logElement.textContent = logs;
						platformSourceContent.appendChild(logElement); // Append logs to platform source content

						if (logs.includes('Generation of platform source-code successful.')) {
							document.getElementById('tick-platformSource').textContent = '✔️'; // Mark platform source as successful
							const platformSourceLoader = document.getElementById('platformSource-loader');
							platformSourceLoader.style.visibility = 'hidden'; // Hide spinner for platform source
							platformSourceContent.classList.add('active'); // Show platform source logs
							platformSourceSection.classList.add('section-success'); // Mark section as success (green)
							isPlatformSourceComplete = true;

							const postProcessingLoader = document.getElementById('postProcessing-loader');
							postProcessingLoader.style.visibility = 'visible'; // Show spinner for post-processing
						} else if (logs.includes('Generation of platform source-code failed.')) {
							document.getElementById('tick-platformSource').textContent = '❌'; // Mark platform source as failed
							const platformSourceLoader = document.getElementById('platformSource-loader');
							platformSourceLoader.style.visibility = 'hidden'; // Hide spinner for platform source
							platformSourceContent.classList.add('active');
							platformSourceSection.classList.add('section-failure');
							isPlatformSourceComplete = true;
						}
					} else if (!isPostProcessingComplete) {
						// Post-processing section handling
						const postProcessingContent = document.getElementById('postProcessingContent');
						const postProcessingSection = document.getElementById('postProcessing').parentElement;

						// Only proceed if platform source-code generation was successful
						const platformSourceSuccess = document.getElementById('tick-platformSource').textContent === '✔️';

						if (platformSourceSuccess) {
							const logElement = document.createElement('pre');
							logElement.textContent = logs;
							postProcessingContent.appendChild(logElement);

							if (logs.includes('Post-processing complete.')) {
								document.getElementById('tick-postProcessing').textContent = '✔️';
								const postProcessingLoader = document.getElementById('postProcessing-loader');
								postProcessingLoader.style.visibility = 'hidden'; // Hide spinner
								postProcessingContent.classList.add('active');
								postProcessingSection.classList.add('section-success');
								isPostProcessingComplete = true;
							}
						}
					}
				}


			</script>


        </body>
        </html>
    `;
}
