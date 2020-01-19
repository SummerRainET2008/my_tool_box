export TOOL_PATH=~/my-tool-box

sudo apt install git
sudo apt install vim
sudo apt install python3-pip
sudo python3 -m pip install numpy

mv ~/.bashrc ~/.bashrc.bak
ln -s $TOOL_PATH/settings/bashrc ~/.bashrc

mv ~/.local_bashrc ~/.local_bashrc.bak
cp $TOOL_PATH/settings/local_bashrc .local_bashrc 

git config --global core.editor "vim"
git config --global diff.tool vimdiff
git config --global credential.helper cache; 
git config --global credential.helper 'cache --timeout=86400'

#git clone https://github.com/SummerRainET2008/my-tool-box.git
