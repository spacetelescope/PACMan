<?php
    // ... upload the file ...

    // ,,open'' the target directory
    $path = "C:/Users/mrams/github/PACMan_private";
    chdir($path);
    $output=shell_exec('python ./test.py');
    echo "<pre>$output</pre>";
?>
