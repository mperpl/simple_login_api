from fastapi import HTTPException, status

def check_credentials(current_user_id, selected_user_id):
    if current_user_id != selected_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized."
        )