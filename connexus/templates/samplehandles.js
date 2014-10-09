// Set starting values
var defaults = [];

// 10-col grid system
defaults[10] = [];
defaults[10][2] = [0, 5, 10];
defaults[10][3] = [0, 3, 7, 10];
defaults[10][4] = [0, 2, 5, 8, 10];
defaults[10][5] = [0, 2, 4, 6, 8, 10];

// 12-col grid system
defaults[12] = [];
defaults[12][2] = [0, 6, 12];
defaults[12][3] = [0, 4, 8, 12];
defaults[12][4] = [0, 3, 6, 9, 12];
defaults[12][5] = [0, 2, 4, 8, 10, 12];

// Set current value
var grid = 10, // Need to set this before finding value from input - 10 or 12
    columns = 5,
    total = 0,
    fraction = '',
    numerator = 0,
    denominator = 0,
    current = $("#my-slider").find('input[name="col[widths]"]').val(),
    values = [];

if ( current ) {
  
  current = current.split('_');
  columns = current.length;

  for ( var i = 0; i <= columns; i++ ) {
    if ( i === 0 ) {
      values[i] = 0;
    } else if ( i == columns ) {
      values[i] = grid;
    } else {
      fraction = current[i-1].split('/');
      total += (grid*fraction[0])/fraction[1];
      values[i] = total;
    }
  }
} else {
  values = defaults[12][3];
}

console.log(values);

$("#my-slider .slider").slider({
  range: 'max',
  min: 0,
  max: grid,
  step: 1,
  values: values,
  slide: function( event, ui ) {
    
    var index = $(ui.handle).index(),
        values = ui.values,
        count = values.length;

    // First and last can't be moved
    if ( index == 1 || index == count ) {
      return false;
    }
    
    var $container = $(ui.handle).closest('.slider-wrap'),
        $option = $container.find('input[name="col[widths]"]'),
        current_val = ui.value,
        next_val = values[index],
        prev_val = values[index-2],
        next_col = 0,
        prev_col = 0,
        prev_col_fraction = '',
        next_col_fraction = '',
        next_numerator = 0,
        prev_numerator = 0,
        prev_final = '',
        final = '';
    
    // Do not allow handles to pass or touch each other
    if ( current_val <= prev_val || current_val >= next_val ) {
      return false;
    }
    
    // Size columns before and after handle
    prev_numerator = current_val-prev_val;
    next_numerator = next_val-current_val;
    prev_col = index-1;
    next_col = index;
    
    // Reduce previous column fraction
    prev_col_fraction = reduce(prev_numerator, grid);
    prev_col_fraction = prev_col_fraction[0].toString()+'/'+prev_col_fraction[1].toString();
    
    // Reduce next column fraction
    next_col_fraction = reduce(next_numerator, grid);
    next_col_fraction = next_col_fraction[0].toString()+'/'+next_col_fraction[1].toString();

    // Set hidden fraction placeholders for reference   
    $container.find('input[name="col['+prev_col+']"]').val(prev_col_fraction);
    $container.find('input[name="col['+next_col+']"]').val(next_col_fraction);
    
    // Update final option
    prev_final = $container.find('input[name="col[widths]"]').val();
    prev_final = prev_final.split('_');
    
    for ( var i = 1; i <= prev_final.length; i++ ) {
      
      if ( i == prev_col ) {
        final += prev_col_fraction;
      } else if ( i == next_col ) {
        final += next_col_fraction;
      } else {
        final += prev_final[i-1]; 
      }
      
      if ( i != prev_final.length ) {
        final += '_';
      }
      
    }
    
    $option.val(final);
    
  }
});

function reduce(numerator, denominator){
  var gcd = function gcd(a,b){
    return b ? gcd(b, a%b) : a;
  };
  gcd = gcd(numerator,denominator);
  return [numerator/gcd, denominator/gcd];
}
