const config = {
    // Look for test files in the "tests/e2e" directory, relative to this configuration file
    testDir: './specs',

    // Each test is given 240 seconds
    timeout: 240000,
    reporter: [
        ['list'],
        ['junit', { outputFile: 'test-results/results.xml' }],
    ],
    // Two retries for each test
    // retries: 2,
    // Configure browser and context here
    use: {
    // video: 'on'
        baseURL: "http://localhost:65432",
        trace: 'retain-on-failure',
        headless: true,
        acceptDownloads: true,
        viewport: { width: 1280, height: 720 },
        ignoreHTTPSErrors: true,
//        launchOptions: {
//            downloadsPath: '/',
//            slowMo: 500,
//        },
        actionTimeout: 30000,
    },
};

module.exports = config;