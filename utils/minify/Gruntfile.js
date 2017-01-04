module.exports = function(grunt)
{
    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        concat: {
            options: {
                // define a string to put between each file in the concatenated output
                separator: '\n /* --- */ \n'
            },
            dist: {
                files: {
                    '../../inginious/frontend/webapp/static/js/all-minified.js': [
                        '../../inginious/frontend/common/static/js/libs/jquery.min.js',
                        '../../inginious/frontend/common/static/js/libs/jquery.form.min.js',
                        '../../inginious/frontend/common/static/js/libs/bootstrap.min.js',
                        '../../inginious/frontend/common/static/js/libs/bootstrap-datetimepicker.min.js',
                        '../../inginious/frontend/common/static/js/libs/checked-list-group.js',
                        '../../inginious/frontend/common/static/js/codemirror/codemirror.js',
                        '../../inginious/frontend/common/static/js/codemirror/mode/meta.js',
                        '../../inginious/frontend/common/static/js/common.js',
                        '../../inginious/frontend/common/static/js/task.js',
                        '../../inginious/frontend/webapp/static/js/jquery-sortable.min.js',
                        '../../inginious/frontend/webapp/static/js/webapp.js',
                        '../../inginious/frontend/webapp/static/js/studio.js',
                        '../../inginious/frontend/webapp/static/js/aggregations.js'
                    ],
                    '../../inginious/frontend/lti/static/js/all-minified.js': [
                        '../../inginious/frontend/common/static/js/libs/jquery.min.js',
                        '../../inginious/frontend/common/static/js/libs/jquery.form.min.js',
                        '../../inginious/frontend/common/static/js/libs/bootstrap.min.js',
                        '../../inginious/frontend/common/static/js/libs/bootstrap-datetimepicker.min.js',
                        '../../inginious/frontend/common/static/js/libs/checked-list-group.js',
                        '../../inginious/frontend/common/static/js/codemirror/codemirror.js',
                        '../../inginious/frontend/common/static/js/codemirror/mode/meta.js',
                        '../../inginious/frontend/common/static/js/common.js',
                        '../../inginious/frontend/common/static/js/task.js',
                        '../../inginious/frontend/lti/static/js/lti.js'
                    ]
                }
            }
        },
        uglify: {
            options: {
                compress: true
            },
            dist: {
                files: {
                    '../../inginious/frontend/webapp/static/js/all-minified.js': ['../../inginious/frontend/webapp/static/js/all-minified.js'],
                    '../../inginious/frontend/lti/static/js/all-minified.js': ['../../inginious/frontend/lti/static/js/all-minified.js']
                }
            }
        }
    });

    // Load the plugin that provides the "uglify" task.
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-compress');

    // Default task(s).
    grunt.registerTask('default', ['concat', 'uglify']);
};
