Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

root = fso.GetParentFolderName(WScript.ScriptFullName)
localDir = fso.BuildPath(root, "_local")
If Not fso.FolderExists(localDir) Then
    fso.CreateFolder(localDir)
End If

outLog = fso.BuildPath(localDir, "web-control-panel.out.log")
errLog = fso.BuildPath(localDir, "web-control-panel.err.log")
command = "cmd.exe /c cd /d " & Chr(34) & root & Chr(34) & " && start " & Chr(34) & "JH-MultiAgent Web" & Chr(34) & " /min python -X utf8 web_control_panel.py --host 127.0.0.1 --port 8765 1> " & Chr(34) & outLog & Chr(34) & " 2> " & Chr(34) & errLog & Chr(34)

shell.Run command, 0, False
WScript.Sleep 1500
shell.Run "http://127.0.0.1:8765/", 1, False
