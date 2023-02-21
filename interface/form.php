<?php
function fill_default($key){
  if(isset($_POST['default'])){
    $default_config = file_get_contents("config_def.json"); //opens the file

    $default_config_data = json_decode($default_config,true);//makes contents into array

    if(is_array($default_config_data[$key])){
      $entry = implode(",", $default_config_data[$key]);
      return $entry;
    }
    else{
      return $default_config_data[$key];
    }
  }
}

function update($key){

  if (isset($_POST['update'])){
    $array_values = ["past_cycles"];
    $int_values = ["close_collaborator_time_frame", "assignment_number_top_reviewers"];
    // check if the config file already exists
    if (file_exists('/Users/mramsahoye/Desktop/PACMan/config.json') == false){
      $default_config = file_get_contents("/Users/mramsahoye/Desktop/PACMan/interface/config_def.json"); //opens the file

      $default_config_data = json_decode($default_config,true);//makes contents into array

      foreach ($default_config_data as $d_key => $d_value) {
        if ($d_key != "help"){
          if(in_array($d_key, $array_values)){
            $array = explode(",", $_POST[$d_key]);
            $default_config_data[$d_key] = $array;
          }else {
            $default_config_data[$d_key] = $_POST[$d_key];
          }
        }
      }

      file_put_contents('/Users/mramsahoye/Desktop/PACMan/config.json', json_encode($default_config_data));

    } else{
      $update_config = file_get_contents("/Users/mramsahoye/Desktop/PACMan/config.json");

      $update_config_data = json_decode($update_config,true);

      //check if the form has changes
      if ($update_config_data[$key] != $_POST[$key]){
        if(in_array($key, $array_values)){
          $array = explode(",", $_POST[$key]);
          $update_config_data[$key] = $array;
          $update = json_encode($update_config_data);
          file_put_contents('/Users/mramsahoye/Desktop/PACMan/config.json', $update);
          return $_POST[$key];
        }else if(in_array($key, $int_values)){
          $val = int($_POST[$key]);
          $update_config_data[$key] = $val;
          $update = json_encode($update_config_data);
          file_put_contents('/Users/mramsahoye/Desktop/PACMan/config.json', $update);
          return $_POST[$key];
        }else {
          $update_config_data[$key] = $_POST[$key];
          $update = json_encode($update_config_data);
          file_put_contents('/Users/mramsahoye/Desktop/PACMan/config.json', $update);
          return $_POST[$key];
        }
      } else{
        if(in_array($key, $array_values)){
          $array = implode(",", $update_config_data[$key]);
          return $array;
        }else {
          return $update_config_data[$key];
        }
      }
    }
  }
}

function update_or_default($key){
    if (isset($_POST['default'])){
      echo fill_default($key);
    }elseif(isset($_POST['update'])){
      echo update($key);}
}

function hover_test($key){
  $default_config = file_get_contents("config_def.json"); //opens the file
  $default_config_data = json_decode($default_config,true);//makes contents into array
 return $default_config_data['help'][$key];
}

?>



<html>

<html lang="en" dir="ltr">

  <head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <meta charset="utf-8">
    <title>PACMan Configuration</title>
  </head>
  <body>
    <form action="" method="POST">
      <h4> Directory names </h4>
      <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("username");?>">Username:</div><input type="text" name="username" value="<?php echo update_or_default("username");?>"/></p>
      <p> <div title="<?php echo hover_test("output_dir");?>">Output directory:</div> <input type="text" name="output_dir" value="<?php echo update_or_default("output_dir");?>"/></p>
      <p> <div title="<?php echo hover_test("results_dir");?>">Results directory:</div> <input type="text" name="results_dir" value="<?php echo update_or_default("results_dir");?>"/></p>
      <p> <div title="<?php echo hover_test("models_dir");?>">Model(s) directory:</div> <input type="text" name="models_dir" value="<?php echo update_or_default("models_dir");?>"/></p>
      </div>
      <input type="hidden" id="PACMan_version" name="PACMan_version" value="0.1">
      <br><br>
      <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("log_dir");?>">Log directory:</div> <input type="text" name="log_dir" value="<?php echo update_or_default("log_dir");?>"/></p>
      <br><div title="<?php echo hover_test("log_level");?>">Log level:</div> <input type="text" name="log_level" value="<?php echo update_or_default("log_level");?>"/>
      <p> <div title="<?php echo hover_test("close_collaborator_time_frame");?>">Time frame (number):</div> <input type="number" name="close_collaborator_time_frame" value="<?php echo update_or_default("close_collaborator_time_frame");?>"/></p>
      <p> <div title="<?php echo hover_test("assignment_number_top_reviewers");?>">Top reviewers(number):</div> <input type="number" name="assignment_number_top_reviewers" value="<?php echo update_or_default("assignment_number_top_reviewers");?>"/></p>
      </div>
      <br><br>
      <h4> PACMan Subscripts </h4>
      <h5> Respond with "true" or "false" to either run or skip certain parts. If a script has completed without error, it does not need to be run again. </h5>
      <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("train");?>">Train?: </div> <input type="text" name="train" value="<?php echo update_or_default("train");?>"/></p>
      <p> <div title="<?php echo hover_test("categorize_one_cycle");?>">Categorize one cycle: </div> <input type="text" name="categorize_one_cycle" value="<?php echo update_or_default("categorize_one_cycle");?>"/></p>
      <p> <div title="<?php echo hover_test("get_science_categories");?>">Get science categories:</div> <input type="text" name="get_science_categories" value="<?php echo update_or_default("get_science_categories");?>"/></p>
      <p> <div title="<?php echo hover_test("compare_results_real");?>">Compare results:</div> <input type="text" name="compare_results_real" value="<?php echo update_or_default("compare_results_real");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("duplication_checker");?>">Duplication check:</div> <input type="text" name="duplication_checker" value="<?php echo update_or_default("duplication_checker");?>"/></p>
      <p> <div title="<?php echo hover_test("categorize_ads_reviewers");?>">Categorize reviewers:</div> <input type="text" name="categorize_ads_reviewers" value="<?php echo update_or_default("categorize_ads_reviewers");?>"/></p>
      <p> <div title="<?php echo hover_test("determine_close_collaborators");?>">Determine close collaborators:</div> <input type="text" name="determine_close_collaborators" value="<?php echo update_or_default("determine_close_collaborators");?>"/></p>
      <p> <div title="<?php echo hover_test("write_conflicts");?>">Write conflicts:</div> <input type="text" name="write_conflicts" value="<?php echo update_or_default("write_conflicts");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("make_assignments");?>">Make assignments:</div> <input type="text" name="make_assignments" value="<?php echo update_or_default("make_assignments");?>"/></p>
      <p> <div title="<?php echo hover_test("cross_validate");?>">Cross validation:</div> <input type="text" name="cross_validate" value="<?php echo update_or_default("cross_validate");?>"/></p>
      <p> <div title="<?php echo hover_test("test_training");?>">Test training:</div> <input type="text" name="test_training" value="<?php echo update_or_default("test_training");?>"/></p>
      <p> <div title="<?php echo hover_test("duplication_checker_need_new_texts");?>">Duplication checker(new texts):</div> <input type="text" name="duplication_checker_need_new_texts" value="<?php echo update_or_default("duplication_checker_need_new_texts");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("duplication_checker_newcycles");?>">Duplication checker(new cycles):</div> <input type="text" name="duplication_checker_newcycles" value="<?php echo update_or_default("duplication_checker_newcycles");?>"/></p>
      <p> <div title="<?php echo hover_test("load_model");?>">Load model?:</div> <input type="text" name="load_model" value="<?php echo update_or_default("load_model");?>"/></p>
      <p> <div title="<?php echo hover_test("load_file");?>">Load corpora file?:</div> <input type="text" name="load_file" value="<?php echo update_or_default("load_file");?>"/></p>
      <p> <div title="<?php echo hover_test("cross_val_score_bal");?>">Cross validate with balanced dataframe:</div> <input type="text" name="cross_val_score_bal" value="<?php echo update_or_default("cross_val_score_bal");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("cross_val_score_raw");?>">Cross validate with total data set:</div> <input type="text" name="cross_val_score_raw" value="<?php echo update_or_default("cross_val_score_raw");?>"/></p>
      <p> <div title="<?php echo hover_test("conf_matrix");?>">Create confusion matrix:</div> <input type="text" name="conf_matrix" value="<?php echo update_or_default("conf_matrix");?>"/></p>
    </div>
    <br><br>
    <h4> Cycle Data </h4>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("main_test_cycle");?>">Main test cycle:</div> <input type="text" name="main_test_cycle" value="<?php echo update_or_default("main_test_cycle");?>"/></p>
      <p> <div title="<?php echo hover_test("past_cycles");?>">Past cycles:</div> <input type="text" name="past_cycles" value="<?php echo update_or_default("past_cycles");?>"/></p>
    </div>
    <br><br>
    <h4> Filepath names </h4>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("scraper_cycles_to_analyze");?>">Scraper cycles to analyze:</div> <input type="text" name="scraper_cycles_to_analyze" value="<?php echo update_or_default("scraper_cycles_to_analyze");?>"/></p>
      <p> <div title="<?php echo hover_test("duplication_checker_corpus_dir");?>">Duplication checker:</div> <input type="text" name="duplication_checker_corpus_dir" value="<?php echo update_or_default("duplication_checker_corpus_dir");?>"/></p>
      <p> <div title="<?php echo hover_test("training_filepath");?>">Training filepath:</div> <input type="text" name="training_filepath" value="<?php echo update_or_default("training_filepath");?>"/></p>
      <p> <div title="<?php echo hover_test("proposal_working_directories");?>">Proposal directories:</div> <input type="text" name="proposal_working_directories" value="<?php echo update_or_default("proposal_working_directories");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("modelfile");?>">Model file:</div> <input type="text" name="modelfile" value="<?php echo update_or_default("modelfile");?>"/></p>
      <p> <div title="<?php echo hover_test("authorfile_suffix");?>">Author file suffix:</div> <input type="text" name="authorfile_suffix" value="<?php echo update_or_default("authorfile_suffix");?>"/></p>
      <p> <div title="<?php echo hover_test("conflict_file_suffix");?>">Reviewer conflicts:</div> <input type="text" name="conflict_file_suffix" value="<?php echo update_or_default("conflict_file_suffix");?>"/></p>
      <p> <div title="<?php echo hover_test("duplication_checker_corpus_suffix");?>">Duplication hashes:</div> <input type="text" name="duplication_checker_corpus_suffix" value="<?php echo update_or_default("duplication_checker_corpus_suffix");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
     <p> <div title="<?php echo hover_test("assignment_rankings_file_suffix");?>">Assignment rankings:</div> <input type="text" name="assignment_rankings_file_suffix" value="<?php echo update_or_default("assignment_rankings_file_suffix");?>"/></p>
      <p> <div title="<?php echo hover_test("assignment_outfile_suffix");?>">Assignment output filename:</div> <input type="text" name="assignment_outfile_suffix" value="<?php echo update_or_default("assignment_outfile_suffix");?>"/></p>
      <p> <div title="<?php echo hover_test("compare_results_by_hand_file");?>">By-hand comparison file:</div> <input type="text" name="compare_results_by_hand_file" value="<?php echo update_or_default("compare_results_by_hand_file");?>"/></p>
      <p> <div title="<?php echo hover_test("comparison_outfile");?>">PACMan vs. By-hand comparison:</div> <input type="text" name="comparison_outfile" value="<?php echo update_or_default("comparison_outfile");?>"/></p>
    </div>
    <br><br>
    <div class="form-check form-check-inline">
      <p> <div title="<?php echo hover_test("training_suffix");?>">Training file suffix:</div> <input type="text" name="training_suffix" value="<?php echo update_or_default("training_suffix");?>"/></p>
      <p> <div title="<?php echo hover_test("train_savefile");?>">Training savefile:</div> <input type="text" name="train_savefile" value="<?php echo update_or_default("train_savefile");?>"/></p>
      <p> <div title="<?php echo hover_test("cross_validate_savefile");?>">Cross validation savefile:</div> <input type="text" name="cross_validate_savefile" value="<?php echo update_or_default("cross_validate_savefile");?>"/></p>

</div>
<br><br>
      <input type="submit" formaction="" name="update" value="Update"/>

      <input type="submit" formaction="" name="default" value="Default"/>

      <input type="submit" formaction="form_run.php" name="run" value="Run"/>

    </form>

  </body>

</html>
