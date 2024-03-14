This program uses the library `instrument_driver` in order to communicate with the instrumentation. This library is present in this repository as a git submodule, as such, when you clone the repository for this program, you must do an extra step:

> `git clone https://github.com/DeltaLabo/tvce.git`
> `git submodule add https://github.com/username/library-repo.git`

This will clone the latest version of the library into the cloned folder.

If there is a change pushed to the library repository and you wish to update the version in the cloned folder of this program, you must do the following:

> `git submodule update --remote`

Any questions regarding **the library** contact Jairo at <jairo.rb8@gmail.com>. 
