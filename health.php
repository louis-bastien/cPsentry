<?php
header('Content-Type: application/json');

//Db information
$host = 'localhost';
$user = 'healthuser';
$pass = 'StrongPassword1234';
$db   = 'healthcheck_db';

// Turn on mysqli exceptions so we can catch them
mysqli_report(MYSQLI_REPORT_STRICT);

//Default status that will be updated if an error is found
$status = "OK";
$mysql = "OK";

try {
    // Replace with your actual credentials
    $conn = mysqli_connect($host, $user, $pass, $db);

    // Test a simple query
    if (!mysqli_query($conn, "SELECT 1")) {
        $mysql = "FAIL: Query error";
    }

    mysqli_close($conn);

} catch (mysqli_sql_exception $e) {
    $mysql = "FAIL: " . $e->getMessage();
}

//Function to iterate over all files in the mail queue and count them
function count_exim_queue_files($path) {
    $total_files = 0;

    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($path, RecursiveDirectoryIterator::SKIP_DOTS),
        RecursiveIteratorIterator::LEAVES_ONLY
    );

    foreach ($iterator as $file) {
        $total_files++;
    }

    return $total_files / 2; // Each email has 2 files and there is an extra file (unknown)
}

$mailqueue = (int) count_exim_queue_files('/var/spool/exim/input/');

$loads = sys_getloadavg();
$load5 = number_format($loads[1], 2, '.', ''); //get the 5min avg loads with 2 decimals

// Disk space check for "/" and "/tmp"
$root_total = disk_total_space("/");
$root_free = disk_free_space("/");
$root_used = $root_total - $root_free;
$root_usage = number_format(($root_used / $root_total) * 100, 2, '.', ''); // Percentage used

$tmp_total = disk_total_space("/tmp");
$tmp_free = disk_free_space("/tmp");
$tmp_used = $tmp_total - $tmp_free;
$tmp_usage = number_format(($tmp_used / $tmp_total) * 100, 2, '.', ''); // Percentage used

//Print the results of the health check
echo json_encode([
    "status"    => "OK",
    "mysql"     => $mysql,
    "mailqueue" => $mailqueue,
    "load" => $load5,
    "rootfs" => $root_usage,
    "tmpfs" => $tmp_usage,
]);