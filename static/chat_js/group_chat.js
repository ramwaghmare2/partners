let selectedMembers = [];

    document.addEventListener("DOMContentLoaded", function() {
        document.querySelectorAll(".add-user-btn").forEach(button => {
            button.addEventListener("click", function() {
                let userId = this.getAttribute("data-user-id");
                let userName = this.getAttribute("data-user-name");
                let userMobile = this.getAttribute("data-user-mobile"); // Keep consistent with 'mobile'
                let userRole = this.getAttribute("data-user-role");

                console.log("User ID:", userId);
                console.log("User Name:", userName);
                console.log("User Mobile:", userMobile);
                console.log("User Role:", userRole);

                // Ensure uniqueness via mobile number
                if (!selectedMembers.some(member => member.mobile === userMobile)) {
                    selectedMembers.push({
                        userid: userId,
                        name: userName,
                        mobile: userMobile, // Use 'mobile' consistently
                        role: userRole
                    });
                    updateSelectedMembers();
                }
            });
        });

        document.getElementById("createGroupBtn").addEventListener("click", function() {
            let groupName = document.getElementById("groupName").value;
            let description = document.getElementById("groupDescription").value;
        
            // Get the file input element for the group photo
            let groupPhotoInput = document.getElementById("groupPhoto");
            let groupPhotoFile = groupPhotoInput.files[0];
            let groupPhotoBase64 = null;
        
            // If a file is selected, convert it to base64
            if (groupPhotoFile) {
                let reader = new FileReader();
                reader.onloadend = function() {
                    groupPhotoBase64 = reader.result;
                    submitGroupData();
                };
                reader.readAsDataURL(groupPhotoFile);  // Convert image to base64
            } else {
                submitGroupData();
            }
        
            // Submit the group data to the server
            function submitGroupData() {
                if (!groupName || selectedMembers.length === 0) {
                    alert("Please enter a group name and select at least one member.");
                    return;
                }
        
                let groupData = {
                    group_name: groupName,
                    description: description,
                    members: selectedMembers.map(member => ({
                        id: member.userid,
                        mobile: member.mobile, // Use 'mobile' instead of 'contact'
                        role: member.role
                    }))
                };
        
                // If a photo was selected, include it in the group data
                if (groupPhotoBase64) {
                    groupData.group_photo = groupPhotoBase64;
                }
        
                // Send the request
                fetch("/chat/create_group", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(groupData)
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    location.reload();  // Reload the page after group creation
                })
                .catch(error => console.error("Error:", error));
            }
        });
        
    });

    function updateSelectedMembers() {
        let container = document.getElementById("selectedMembers");
        container.innerHTML = "";

        selectedMembers.forEach(member => {
            let div = document.createElement("div");
            div.classList.add("d-flex", "justify-content-between", "align-items-center", "mb-1");
            div.innerHTML = `
                <span>${member.name} (${member.mobile})</span>
                <button type="button" class="btn btn-danger btn-sm" onclick="removeMember('${member.mobile}')">
                    <i class="fas fa-minus"></i>
                </button>
            `;
            container.appendChild(div);
        });
    }

    function removeMember(mobile) {
        selectedMembers = selectedMembers.filter(member => member.mobile !== mobile);
        updateSelectedMembers();
    }